"""Data structures used by other packages. """

# TODO: check serialisation of phrases/clause
# TODO: check deepcopy
# TODO: create module `element_algebra` and pud add/iadd into it


import collections
import json

from copy import deepcopy
from functools import wraps

from nlglib.features import NON_COMPARABLE_FEATURES, TRANSFERABLE_FEATURES
from nlglib.features import FeatureSet, DISCOURSE_FUNCTION, category


_sentinel = object()


# noinspection PyShadowingBuiltins
class Element(object):
    """A base class representing an NLG element.
        Aside for providing a base class for other kinds of NLG elements,
        the class also implements basic functionality for elements.

    """

    category = category.ELEMENT

    def __init__(self, features=None, parent=None, id=None):
        self.features = FeatureSet()
        self.features.update(features)
        self.parent = parent
        self.id = id
        self.hash = -1

    def __copy__(self):
        rv = self.__class__(features=self.features,
                            parent=self.parent,
                            id=self.id)
        return rv

    # noinspection PyArgumentList
    def __deepcopy__(self, memo):
        rv = self.__class__(features=None,
                            parent=None,
                            id=self.id)
        memo[id(self)] = rv
        rv.features = deepcopy(self.features, memo=memo)
        rv.parent = memo.get(id(self.parent), None)
        return rv

    def __bool__(self):
        """Because Element is abstract, it will evaluate to false. """
        return False

    def __eq__(self, other):
        return (isinstance(other, Element) and
                self.id == other.id and
                self.category == other.category and
                comparable_features(self.features) ==
                comparable_features(other.features))

    def __hash__(self):
        if self.hash == -1:
            self.hash = hash(str(self))
        return self.hash

    def __repr__(self):
        from . import visitors
        v = visitors.ReprVisitor()
        self.accept(v)
        return str(v)

    def __str__(self):
        from . import visitors
        v = visitors.SimpleStrVisitor()
        self.accept(v)
        return str(v)

    def __contains__(self, feature_name):
        """Check if the argument feature name is contained in the element."""
        return feature_name in self.features

    def __setitem__(self, feature_name, feature_value):
        """Set the feature name/value in the element feature set."""
        self.features[feature_name] = feature_value

    def __getitem__(self, feature_name):
        """Return the value associated with the feature name, from the
        element feature set.

        If the feature name is not found in the feature dict, return None.

        """
        return self.features.get(feature_name)

    def __delitem__(self, feature_name):
        """Remove the argument feature name and its associated value from
        the element feature set.

        """
        self.features.discard(feature_name)

    def __add__(self, other):
        """Add two elements resulting in a coordination 
        if both elements are not "False" else return the "True" element.
        
        """
        if not self:
            return other
        if not other:
            return self
        return Coordination(self, other)

    @classmethod
    def from_dict(cls, dct):
        o = cls(None, None, None)
        o.__dict__.update(dct)
        return o

    @classmethod
    def from_json(cls, s):
        return json.loads(s, cls=ElementDecoder)

    def to_json(self):
        return json.dumps(self, cls=ElementEncoder)

    def to_xml(self, depth=0, headers=False):
        from . import visitors
        visitor = visitors.XmlVisitor(depth=depth)
        self.accept(visitor)
        if headers:
            return str(visitor)
        else:
            return str(visitor.xml)

    def accept(self, visitor, **kwargs):
        """Implementation of the Visitor pattern."""
        visitor_method_name = self.category.lower()
        # get the appropriate method of the visitor instance
        m = getattr(visitor, visitor_method_name)
        # ensure that the method is callable
        if not hasattr(m, '__call__'):
            msg = 'Error: cannot call undefined method: %s on visitor'
            raise ValueError(msg % visitor_method_name)
        # and finally call the callback
        return m(self, **kwargs)

    def elements(self, recursive=False, itself=None):
        """Return a generator yielding elements contained in the element

        :param bool recursive: also include sub-elements of the contained elements
        :param str itself: yield `self` as one of the elements; values in (None, 'first', 'last')

        """
        if itself or recursive and self.category != category.ELEMENT:
            yield self

    def arguments(self):
        """Return any arguments (vars) from the element as a list. """
        return [x for x in self.elements(recursive=True) if x.category == category.VAR]

    def replace(self, one, another, key=lambda x: x):
        """Replace the first occurrence of `one` by `another`.

        :param one: a constituent to replace; will be raised to element
        :param another: a replacement element; will be raised to element
        :param key: a key function for comparison; default is identity
        :returns: True if replacement occurred; False otherwise
        
        """
        return False  # basic implementation does nothing

    def replace_argument(self, id, replacement):
        """Replace an argument with given `id` by `replacement`
        if such argument exists.

        """
        for a in self.arguments():
            if a.id == id:
                return self.replace(a, replacement)
        return False

    def replace_arguments(self, **kwargs):
        """Replace arguments with ids in the kwargs 
        by the corresponding values. 
        
        """
        for k, v in kwargs.items():
            self.replace_argument(k, v)

    @property
    def string(self):
        """Return the string inside the value. """
        return ''

    def update_parents(self, parent=_sentinel):
        """Re-set the `parent` attribute of nested elements."""
        if parent is not _sentinel:
            self.parent = parent


# decorator
def str_or_element(fn):
    @wraps(fn)
    def helper(word, features=None):
        if isinstance(word, str):
            return fn(word, features=features)
        elif isinstance(word, Element):
            tmp = fn(str(word), features=features)
            word.features.update(tmp.features)
            return word
        else:
            return fn(str(word), features=features)
    return helper


class ElementList(collections.UserList):
    category = category.ELEMENT_LIST

    def __init__(self, lst=None, parent=None, features=FeatureSet()):
        super().__init__()
        self.parent = parent
        self.features = FeatureSet()
        self.features.update(features)
        for o in lst or []:
            self.append(o)

    def append(self, item):
        item = raise_to_element(item)
        item.parent = self.parent
        item.features.update(self.features)
        super().append(item)

    def insert(self, i, item):
        item = raise_to_element(item)
        item.parent = self.parent
        item.features.update(self.features)
        super().insert(i, item)

    def remove(self, item):
        raised_item = raise_to_element(item)
        super().remove(raised_item)

    def __contains__(self, item):
        raised_item = raise_to_element(item)
        return super().__contains__(raised_item)

    def __iadd__(self, other):
        if isinstance(other, (ElementList, list, tuple)):
            for x in other:
                self.append(x)
        else:
            self.append(other)
        return self

    def __add__(self, other):
        rv = ElementList(self, parent=self.parent, features=self.features)
        rv += other
        return rv

    def __setitem__(self, i, value):
        value = raise_to_element(value)
        value.parent = self.parent
        value.features.update(self.features)
        super().__setitem__(i, value)

    # noinspection PyArgumentList
    def __deepcopy__(self, memo):
        rv = self.__class__()
        memo[id(self)] = rv
        rv.parent = memo.get(id(self.parent), None)
        rv.features = deepcopy(self.features, memo)
        for o in self.data:
            rv.data.append(deepcopy(o, memo))
        return rv

    @classmethod
    def from_dict(cls, dct):
        o = cls()
        o.__dict__.update(dct)
        return o

    @classmethod
    def from_json(cls, s):
        return json.loads(s, cls=ElementDecoder)

    def to_json(self):
        return json.dumps(self, cls=ElementEncoder)

    def elements(self, recursive=False, itself=None):
        """Return a generator yielding elements contained in the element

        Note that ElementList is a pseudo-element so it doesn't return
        itself even if the param is specified.

        :param bool recursive: also include sub-elements of the contained elements
        :param str itself: yield `self` as one of the elements; values in (None, 'first', 'last')

        """
        if recursive:
            for e in self:
                yield from e.elements(recursive, itself)
        else:
            for e in self:
                yield e

    def update_parents(self, parent=_sentinel):
        if parent is not _sentinel:
            self.parent = parent
        for x in self:
            x.update_parents(parent=parent)


class Var(Element):
    """An element used as a place-holder in a sentence. The purpose of this
        element is to make replacing arguments easier. For example, in a plan
        one might want to replace arguments of an action with the instantiated
        objects
        E.g.,   move (x, a, b) -->
                move Var(x) from Var(a) to Var(b) -->
                move (the block) from (the table) to (the green block)

    """

    category = category.VAR

    def __init__(self, id=None, obj=None, features=None, parent=None):
        super().__init__(features, parent, id)
        self.value = None
        self.set_value(obj)

    def __bool__(self):
        """Return True """
        return True

    def __eq__(self, other):
        return super().__eq__(other) and self.value == other.value

    def __hash__(self):
        if self.hash == -1:
            self.hash = hash(str(self))
        return self.hash

    def __copy__(self):
        return self.__class__(self.id, self.value, self.features, self.parent)

    # noinspection PyArgumentList
    def __deepcopy__(self, memo):
        rv = self.__class__(self.id, self.value)
        memo[id(self)] = rv
        rv.features = deepcopy(self.features, memo=memo)
        rv.parent = memo.get(id(self.parent), None)
        return rv

    def set_value(self, val):
        if val is None: val = Word(str(self.id), 'NOUN')
        self.value = String(val) if isinstance(val, str) else val

    @property
    def string(self):
        """Return the string inside the value. """
        return self.value.string


class String(Element):
    """String is a basic element representing canned text. """

    category = category.STRING

    def __init__(self, value='', features=None, parent=None, id=None):
        super().__init__(features, parent, id)
        self.value = str(value)

    def __bool__(self):
        """Return True if the string is non-empty. """
        return len(self.value) > 0

    def __eq__(self, other):
        return super().__eq__(other) and self.value == other.value

    def __hash__(self):
        if self.hash == -1:
            self.hash = hash(str(self))
        return self.hash

    def __copy__(self):
        return self.__class__(self.value, self.features, self.parent, self.id)

    # noinspection PyArgumentList
    def __deepcopy__(self, memo):
        rv = self.__class__(self.value, None, None, self.id)
        memo[id(self)] = rv
        rv.features = deepcopy(self.features, memo=memo)
        rv.parent = memo.get(id(self.parent), None)
        return rv

    @property
    def string(self):
        """Return the string inside the value. """
        return self.value


class Word(Element):
    """Word represents word and its corresponding POS (Part-of-Speech) tag. """

    category = category.WORD

    def __init__(self, word, pos=None, features=None, parent=None, id=None):
        super().__init__(features, parent, id)
        self.word = str(word)
        self.pos = pos or category.ANY
        self.do_inflection = False

    def __bool__(self):
        """Return True """
        return True

    def __eq__(self, other):
        return super().__eq__(other) and self.word == other.word and self.pos == other.pos

    def __hash__(self):
        if self.hash == -1:
            self.hash = hash(str(self))
        return self.hash

    def __copy__(self):
        # pos is in features
        return self.__class__(self.word, pos=self.pos, features=self.features,
                              parent=self.parent, id=self.id)

    # noinspection PyArgumentList
    def __deepcopy__(self, memo):
        # pos is in features
        rv = self.__class__(self.word, pos=self.pos, features=None,
                            parent=None, id=self.id)
        memo[id(self)] = rv
        rv.features = deepcopy(self.features, memo=memo)
        rv.parent = memo.get(id(self.parent), None)
        return rv

    @property
    def string(self):
        """Return the word. """
        return self.word


class Coordination(Element):
    """Coordinated clause with a conjunction. 
    
    The class enforces that the coordinates are of the same type.
    
    """

    category = category.COORDINATION

    def __init__(self, *coords, conj=None, features=None, parent=None, id=None):
        super().__init__(features, parent, id)
        self.coords = ElementList(parent=self)
        self.add_coordinates(*coords)
        self.coordinate_category = self.coords[0].category if self.coords else None
        if conj is not None:
            self.conj = raise_to_element(conj)
        else:
            self.conj = String('and')

    def __len__(self):
        return len(self.coords)

    def __eq__(self, other):
        return super().__eq__(other) and self.coords == other.coords

    def __hash__(self):
        if self.hash == -1:
            self.hash = hash(str(self))
        return self.hash

    def __copy__(self):
        return self.__class__(*self.coords, conj=self.conj, features=self.features,
                              parent=self.parent, id=self.id)

    # noinspection PyArgumentList
    def __deepcopy__(self, memo):
        # pos is in features
        rv = self.__class__(features=None, parent=None, id=self.id)
        memo[id(self)] = rv
        rv.conj = deepcopy(self.conj, memo=memo)
        rv.features = deepcopy(self.features, memo=memo)
        rv.coords = deepcopy(self.coords, memo=memo)
        rv.parent = memo.get(id(self.parent), None)
        return rv

    def __add__(self, other):
        """Add two elements resulting in a coordination
        if both elements are not "False" else return the "True" element.

        """
        if isinstance(other, Coordination):
            rv = Coordination(self, other, features=deepcopy(self.features))
        else:
            rv = deepcopy(self)
            rv.coords.append(other)
        return rv

    def __iadd__(self, other):
        other.features.discard(DISCOURSE_FUNCTION)
        self.coords.append(other)
        return self

    def __bool__(self):
        return bool(self.coords)

    @property
    def string(self):
        return self.coords[0].string if self.coords else ''

    @staticmethod
    def _reset_parent(coordination):
        """Set the `parent` of coordinates and the list to None.
        
        Necessary for serialising to json.
        
        """
        coordination.coords.parent = None
        for x in coordination.coords:
            x.parent = None
            if x.category == category.COORDINATION:
                Coordination._reset_parent(x)

    def update_parents(self, parent=_sentinel):
        if parent is not _sentinel:
            self.parent = parent
        new_parent = None if parent is None else self
        self.coords.update_parents(new_parent)

    def to_json(self):
        cp = deepcopy(self)
        Coordination._reset_parent(cp)
        return super(Coordination, cp).to_json()

    def add_coordinates(self, *elts):
        """Add one or more elements as a co-ordinate in the clause. """
        for e in [raise_to_element(elt) for elt in elts if elt is not None]:
            self.coords.append(e)
            # cat = self.coords[0].cat
            # if not all(x.coordinate_category == cat \
            #            if isinstance(x, Coordination) else x.cat == cat for x in self.coords):
            #     msg = ('All elements of a coordination have to have '
            #            'the same lexical category ({} but entering {}).')
            #     raise TypeError(msg.format(cat, self.coords[-1].cat))

    def elements(self, recursive=False, itself=None):
        """Return a generator yielding elements contained in the element

        :param bool recursive: also include sub-elements of the contained elements
        :param str itself: yield `self` as one of the elements; values in (None, 'first', 'last')

        """
        if itself == 'first':
            yield self

        for i, e in enumerate(self.coords, start=1):
            if i == len(self.coords) and self.conj:
                if recursive:
                    yield from self.conj.elements(recursive, itself)
                else:
                    if self.conj:
                        yield self.conj
            if recursive:
                yield from e.elements(recursive, itself)
            else:
                yield e

        if itself == 'last':
            yield self

    def replace(self, one, another, key=lambda x: x):
        """Replace first occurrence of `one` with `another`.
        
        Return True if successful, False if `one` not found. 
        Note that the call is recursive on elements within.

        """
        one = raise_to_element(one)
        another = raise_to_element(another)
        for i, o in enumerate(self.coords[:]):
            if key(o) == key(one):
                o.parent = None
                if another:
                    another.parent = self
                    transfer_features(o, another)
                    self.coords[i] = another
                else:
                    del self.coords[i]
                return True
            else:
                if o.replace(one, another):
                    return True
        return False


class Phrase(Element):
    """A base class for all kinds of phrases - elements containing other
        elements in specific places of the construct (pre-, post-
        modifiers as well as the head of the phrase and any complements.

    """

    _head = Element()
    category = category.PHRASE

    def __init__(self, features=None, parent=None, id=None, **kwargs):
        super().__init__(features, parent, id)
        self.premodifiers = (ElementList(parent=self) +
                             kwargs.pop('premodifiers', []))
        self.head = kwargs.pop('head', None)
        self.complements = (ElementList(parent=self) +
                            kwargs.pop('complements', []))
        self.postmodifiers = (ElementList(parent=self) +
                              kwargs.pop('postmodifiers', []))

    def __bool__(self):
        """Return True """
        return any(bool(x) for x in self.elements())

    def __eq__(self, other):
        return (super().__eq__(other) and
                self.premodifiers == other.premodifiers and
                self.head == other.head and
                self.complements == other.complements and
                self.postmodifiers == other.postmodifiers)

    def __hash__(self):
        if self.hash == -1:
            self.hash = hash(str(self))
        return self.hash

    def __copy__(self):
        rv = self.__class__(features=self.features, parent=self.parent,
                            id=self.id)
        rv.head = self.head
        rv.premodifiers = self.premodifiers[:]
        rv.complements = self.complements[:]
        rv.postmodifiers = self.postmodifiers[:]
        return rv

    # noinspection PyArgumentList
    def __deepcopy__(self, memo):
        rv = self.__class__(id=self.id)
        memo[id(self)] = rv
        rv.parent = memo.get(id(self.parent), None)
        rv.features = deepcopy(self.features, memo=memo)
        rv.premodifiers = deepcopy(self.premodifiers, memo=memo)
        rv.head = deepcopy(self.head, memo=memo)
        rv.complements = deepcopy(self.complements, memo=memo)
        rv.postmodifiers = deepcopy(self.postmodifiers, memo=memo)
        return rv

    def __iadd__(self, other):
        if is_adjective_type(other) or is_adverb_type(other):
            self.premodifiers.append(other)
        else:
            self.complements.append(other)
        return self

    @property
    def string(self):
        return self.head.string

    @property
    def head(self):
        return self._head

    @head.setter
    def head(self, value):
        if self._head:
            self._head.parent = None
        if value is not None:
            new_value = raise_to_element(value)
            new_value.parent = self
            self._head = new_value
        else:
            self._head = Element()
        self._head[DISCOURSE_FUNCTION] = DISCOURSE_FUNCTION.head

    def elements(self, recursive=False, itself=None):
        """Return a generator yielding elements contained in the element

        :param bool recursive: also include sub-elements of the contained elements
        :param str itself: yield `self` as one of the elements; values in (None, 'first', 'last')

        """
        if itself == 'first':
            yield self

        yield from self.premodifiers.elements(recursive, itself)
        if recursive:
            yield from self.head.elements(recursive, itself)
        else:
            if self.head != Element():
                yield self.head
        yield from self.complements.elements(recursive, itself)
        yield from self.postmodifiers.elements(recursive, itself)

        if itself == 'last':
            yield self

    def _replace_in_list(self, lst, one, another, key):
        for i, o in enumerate(lst):
            if key(o) == key(one):
                if another is None:
                    lst[i].parent = None
                    del lst[i]
                else:
                    another.parent = self
                    transfer_features(lst[i], another)
                    lst[i] = another
                return True
            else:
                if o.replace(one, another, key):
                    return True
        return False

    def replace(self, one, another, key=lambda x: x):
        """Replace first occurrence of `one` with `another`.
        
        Return True if successful.

        """

        one = raise_to_element(one)
        another = raise_to_element(another)

        if self._replace_in_list(self.premodifiers, one, another, key):
            return True
        # TODO: unify when replacement is a phrase of the same kind?
        if key(self.head) == key(one):
            self.head.parent = None
            for k in self.head.features.keys():
                if k in self.features:
                    del self.features[k]
            transfer_features(self.head, another)
            self.head = another
            self.features.update(another.features)
            return True
        if self.head.replace(one, another, key):
            return True
        if self._replace_in_list(self.complements, one, another, key):
            return True
        if self._replace_in_list(self.postmodifiers, one, another, key):
            return True
        return False

    def update_parents(self, parent=_sentinel):
        if parent is not _sentinel:
            self.parent = parent
        to_update = [
            self.premodifiers,
            self.head,
            self.complements,
            self.postmodifiers,
        ]
        new_parent = None if parent is None else self
        for o in to_update:
            o.update_parents(parent=new_parent)


class NounPhrase(Phrase):
    """
     * Specifier     (eg, "the")
     * PreModifier   (eg, "green")
     * Noun (head)   (eg, "apples")
     * complement    (eg, "that you liked")
     * PostModifier  (eg, "in the shop")
     
     """

    _spec = Element()
    category = category.NOUN_PHRASE

    def __init__(self, head=None, specifier=None, features=None,
                 parent=None, id=None, **kwargs):
        super().__init__(features, parent, id, **kwargs)
        self.specifier = specifier
        self.head = head

    def __eq__(self, other):
        return (super().__eq__(other) and
                self.specifier == other.specifier and
                self.head == other.head)

    def __hash__(self):
        if self.hash == -1:
            self.hash = hash(str(self))
        return self.hash

    def __copy__(self):
        rv = self.__class__(self.head, self.specifier, features=self.features,
                            parent=self.parent, id=self.id)
        rv.premodifiers = self.premodifiers[:]
        rv.complements = self.complements[:]
        rv.postmodifiers = self.postmodifiers[:]
        return rv

    # noinspection PyArgumentList
    def __deepcopy__(self, memo):
        rv = super().__deepcopy__(memo=memo)
        rv.specifier = deepcopy(self.specifier, memo=memo)
        return rv

    @property
    def specifier(self):
        return self._spec

    @specifier.setter
    def specifier(self, value):
        if self.specifier:
            self._spec.parent = None
        if value:
            new_value = raise_to_element(value)
            new_value.parent = self
            self._spec = new_value
        else:
            self._spec = Element()
        self._spec[DISCOURSE_FUNCTION] = DISCOURSE_FUNCTION.specifier

    def elements(self, recursive=False, itself=None):
        """Return a generator yielding elements contained in the element

        :param bool recursive: also include sub-elements of the contained elements
        :param str itself: yield `self` as one of the elements; values in (None, 'first', 'last')

        """
        if itself == 'first':
            yield self

        if recursive:
            yield from self.specifier.elements(recursive, itself)
        else:
            if self.specifier != Element():
                yield self.specifier
        yield from self.premodifiers.elements(recursive, itself)
        if recursive:
            yield from self.head.elements(recursive, itself)
        else:
            if self.head != Element():
                yield self.head
        yield from self.complements.elements(recursive, itself)
        yield from self.postmodifiers.elements(recursive, itself)

        if itself == 'last':
            yield self

    def replace(self, one, another, key=lambda x: x):
        """Replace first occurrence of one with another.
        Return True if successful.

        """
        one = raise_to_element(one)
        another = raise_to_element(another)

        if key(self.specifier) == key(one):
            self.specifier.parent = None
            another.parent = self
            transfer_features(self.specifier, another)
            self.specifier = another
            return True
        if self.specifier.replace(one, another, key):
            return True
        return super().replace(one, another, key)

    def update_parents(self, parent=_sentinel):
        if parent is not _sentinel:
            self.parent = parent
        new_parent = None if parent is None else self
        self.specifier.update_parents(new_parent)
        super().update_parents(parent)


class VerbPhrase(Phrase):
    """
     * PreModifier      (eg, "reluctantly")
     * Verb             (eg, "gave")
     * IndirectObject   (eg, "Mary")
     * Object           (eg, "an apple")
     * PostModifier     (eg, "before school")

     """

    category = category.VERB_PHRASE

    def __init__(self, head=None, *compl, features=None, parent=None, **kwargs):
        super().__init__(features, parent, **kwargs)
        self.head = head
        self.complements += compl
        if 'object' in kwargs:
            self.object = kwargs.pop('object')
        if 'indirect_object' in kwargs:
            self.indirect_object = kwargs.pop('indirect_object')

    @property
    def object(self):
        for c in self.complements:
            if c[DISCOURSE_FUNCTION] == DISCOURSE_FUNCTION.object:
                return c
        return None

    @object.setter
    def object(self, value):
        to_remove = [c for c in self.complements
                     if c[DISCOURSE_FUNCTION] == DISCOURSE_FUNCTION.object]
        for c in to_remove:
            self.complements.remove(c)
        if value is None:
            return
        new_value = raise_to_element(value)
        new_value.parent = self
        new_value[DISCOURSE_FUNCTION] = DISCOURSE_FUNCTION.object
        self.complements.append(new_value)

    @property
    def indirect_object(self):
        for c in self.complements:
            if c[DISCOURSE_FUNCTION] == DISCOURSE_FUNCTION.indirect_object:
                return c
        return None

    @indirect_object.setter
    def indirect_object(self, value):
        to_remove = [c for c in self.complements
                     if c[DISCOURSE_FUNCTION] == DISCOURSE_FUNCTION.indirect_object]
        for c in to_remove:
            self.complements.remove(c)
        if value is None:
            return
        new_value = raise_to_element(value)
        new_value.parent = self
        new_value[DISCOURSE_FUNCTION] = DISCOURSE_FUNCTION.indirect_object
        self.complements.insert(0, new_value)


class PrepositionPhrase(Phrase):
    category = category.PREPOSITION_PHRASE

    def __init__(self, head=None, *compl, features=None, parent=None, **kwargs):
        super().__init__(features, parent, **kwargs)
        self.head = head
        self.complements += compl


class AdverbPhrase(Phrase):
    category = category.ADVERB_PHRASE

    def __init__(self, head=None, *compl, features=None, parent=None, **kwargs):
        super().__init__(features, parent, **kwargs)
        self.head = head
        self.complements += compl


class AdjectivePhrase(Phrase):
    category = category.ADJECTIVE_PHRASE

    def __init__(self, head=None, *compl, features=None, parent=None, **kwargs):
        super().__init__(features, parent, **kwargs)
        self.head = head
        self.complements += compl


class Clause(Phrase):
    """Clause - sentence.
    From simplenlg:

    * FrontModifier (eg, "Yesterday")
    * Subject (eg, "John")
    * PreModifier (eg, "reluctantly")
    * Verb (eg, "gave")
    * IndirectObject (eg, "Mary")
    * Object (eg, "an apple")
    * PostModifier (eg, "before school")
    
    Note that verb, indirect object, and object
    are propagated to the underlying verb phrase

    """

    _subject = None
    _predicate = None
    category = category.CLAUSE

    def __init__(self, subject=None, predicate=None, objekt=None,
                 features=None, parent=None, **kwargs):
        super().__init__(features, parent=parent, **kwargs)
        fm = kwargs.pop('front_modifiers', [])
        self.front_modifiers = ElementList(parent=self) + fm
        self.subject = subject
        self.predicate = predicate
        if objekt:
            self.object = objekt

    def __eq__(self, other):
        return (super().__eq__(other) and
                self.premodifiers == other.premodifiers and
                self.subject == other.subject and
                self.predicate == other.predicate and
                self.complements == other.complements and
                self.postmodifiers == other.postmodifiers)

    def __hash__(self):
        if self.hash == -1:
            self.hash = hash(str(self))
        return self.hash

    def __add__(self, other):
        other_ = deepcopy(other)
        self_ = deepcopy(self)
        if isinstance(other, Clause):
            return Coordination(self_, other_)
        if is_adjective_type(other):
            self_.subject += other_
            return self_
        if is_adverb_type(other):
            self_.predicate += other_
            return self_
        else:
            msg = 'Cannot add these up: "{}" + "{}"'
            raise ValueError(msg.format(self, other))

    def __copy__(self):
        rv = self.__class__(features=self.features, parent=self.parent,
                            id=self.id)
        rv.front_modifiers = self.front_modifiers[:]
        rv.subject = self.subject
        rv.premodifiers = self.premodifiers[:]
        rv.predicate = self.predicate
        rv.complements = self.complements[:]
        rv.postmodifiers = self.postmodifiers[:]
        return rv

    # noinspection PyArgumentList
    def __deepcopy__(self, memo):
        rv = self.__class__(id=self.id)
        memo[id(self)] = rv
        rv.parent = memo.get(id(self.parent), None)
        rv.features = deepcopy(self.features, memo=memo)
        rv.front_modifiers = deepcopy(self.front_modifiers, memo=memo)
        rv.subject = deepcopy(self.subject, memo=memo)
        rv.premodifiers = deepcopy(self.premodifiers, memo=memo)
        rv.predicate = deepcopy(self.predicate, memo=memo)
        rv.complements = deepcopy(self.complements, memo=memo)
        rv.postmodifiers = deepcopy(self.postmodifiers, memo=memo)
        return rv

    @property
    def string(self):
        return self.subject.string or self.predicate.string

    @property
    def subject(self):
        return self._subject

    @subject.setter
    def subject(self, value):
        if self._subject:
            self._subject.parent = None
            del self._subject[DISCOURSE_FUNCTION]
        if value is not None:
            new_value = raise_to_np(value)
            new_value.parent = self
            self._subject = new_value
        else:
            self._subject = Element()
        self._subject[DISCOURSE_FUNCTION] = DISCOURSE_FUNCTION.subject

    @property
    def predicate(self):
        return self._predicate

    @predicate.setter
    def predicate(self, value):
        if self._predicate:
            self._predicate.parent = None
            del self._predicate[DISCOURSE_FUNCTION]
        if value is not None:
            new_value = raise_to_vp(value)
            new_value.parent = self
            self._predicate = new_value
        else:
            self._predicate = Element()
        self._predicate[DISCOURSE_FUNCTION] = DISCOURSE_FUNCTION.predicate

    @property
    def head(self):
        return self.predicate

    @head.setter
    def head(self, value):
        self.predicate = value

    @property
    def verb(self):
        # noinspection PyUnresolvedReferences
        return self.predicate.head if self.predicate else None

    @verb.setter
    def verb(self, value):
        if self.predicate:
            self.predicate.head = raise_to_element(value)
        else:
            self.predicate = raise_to_vp(value)

    @property
    def object(self):
        # noinspection PyUnresolvedReferences
        return self.predicate.object if self.predicate else None

    @object.setter
    def object(self, value):
        if not self.predicate:
            self.predicate = VerbPhrase(parent=self)
        self.predicate.object = value

    @property
    def indirect_object(self):
        # noinspection PyUnresolvedReferences
        return self.predicate.indirect_object if self.predicate else None

    @indirect_object.setter
    def indirect_object(self, value):
        if not self.predicate:
            self.predicate = VerbPhrase(parent=self)
        self.predicate.indirect_object = value

    def elements(self, recursive=False, itself=None):
        """Return a generator yielding elements contained in the element

        :param bool recursive: also include sub-elements of the contained elements
        :param str itself: yield `self` as one of the elements; values in (None, 'first', 'last')

        """
        if itself == 'first':
            yield self

        yield from self.front_modifiers.elements(recursive, itself)
        if recursive:
            yield from self.subject.elements(recursive, itself)
        else:
            if self.subject != NounPhrase(parent=self):
                yield self.subject
        yield from self.premodifiers.elements(recursive, itself)
        if recursive:
            yield from self.predicate.elements(recursive, itself)
        else:
            if self.predicate != VerbPhrase(parent=self):
                yield self.predicate
        yield from self.complements.elements(recursive, itself)
        yield from self.postmodifiers.elements(recursive, itself)

        if itself == 'last':
            yield self

    def replace(self, one, another, key=lambda x: x):
        """Replace first occurrence of `one` with `another` and
        return True if successful.

        """
        one = raise_to_element(one)
        another = raise_to_element(another)

        if key(self.subject) == key(one):
            transfer_features(self.subject, another)
            self.subject = another
            return True
        if self.subject.replace(one, another, key):
            return True

        if key(self.predicate) == key(one):
            transfer_features(self.predicate, another)
            self.predicate = another
            return True
        if self.predicate.replace(one, another, key):
            return True

        return super().replace(one, another, key)

    def update_parents(self, parent=_sentinel):
        if parent is not _sentinel:
            self.parent = parent
        new_parent = None if parent is None else self
        to_update = [self.front_modifiers, self.subject, self.predicate]
        for x in to_update:
            x.update_parents(new_parent)
        super().update_parents(parent)


def is_adjective_type(element, strict=False):
    """Return True if `element` is adjective modifier (adj or AdjP)"""
    check = all if strict else any
    return (isinstance(element, AdjectivePhrase) or
            isinstance(element, Word) and element.pos == category.ADJECTIVE or
            isinstance(element, Coordination) and
            check(is_adjective_type(c) for c in element.coords))


def is_adverb_type(element, strict=False):
    """Return True if `element` is adverb modifier (adv or AdvP)"""
    check = all if strict else any
    return (isinstance(element, AdverbPhrase) or
            isinstance(element, Word) and element.pos == category.ADVERB or
            isinstance(element, Coordination)
            and check(is_adverb_type(c) for c in element.coords))


def is_noun_type(element, strict=False):
    """Return True if `element` is adverb modifier (adv or AdvP)"""
    check = all if strict else any
    return (isinstance(element, NounPhrase) or
            isinstance(element, Word) and element.pos == category.NOUN or
            isinstance(element, Coordination)
            and check(is_noun_type(c) for c in element.coords))


def is_verb_type(element, strict=False):
    """Return True if `element` is adverb modifier (adv or AdvP)"""
    check = all if strict else any
    return (isinstance(element, VerbPhrase) or
            isinstance(element, Word) and element.pos == category.VERB or
            isinstance(element, Coordination)
            and check(is_verb_type(c) for c in element.coords))


def is_element_type(element):
    """Return True if `element` is an instance of `Element`."""
    return isinstance(element, Element)


def is_phrase_type(element, strict=False):
    """Return True if `element` is a phrase. """
    check = all if strict else any
    if isinstance(element, Coordination):
        return check(is_phrase_type(c) for c in element.coords)
    return isinstance(element, Phrase)


def is_clause_type(element, strict=False):
    """An object is a clause type if it is a clause, subordination or
    a coordination of clauses.

    """
    check = all if strict else any
    if isinstance(element, Coordination):
        return check(is_clause_type(c) for c in element.coords)
    return isinstance(element, Clause)


def raise_to_element(element):
    """Raise the given thing to an element (e.g., String). """
    if element is None:
        return Element()
    if not isinstance(element, Element):
        return String(element)
    return element


def raise_to_np(element):
    """Take the current phrase and raise it to an NP.
    If `phrase` is a Noun it will be promoted to NP and used as a head;
    If `phrase` is a CC its coordinates will be raised to NPs

    """
    element = raise_to_element(element)
    if isinstance(element, Coordination):
        element.coords = ElementList([raise_to_np(c) for c in element.coords])
        return element
    if isinstance(element, (String, Word)):
        return NounPhrase(head=element)
    if isinstance(element, Element) and element.category == category.ELEMENT:
        return NounPhrase(head=element)
    return element


def raise_to_vp(element):
    """Take the current phrase and raise it to a VP.
    If `phrase` is a Word it will be promoted to VP and used as a head;
    If `phrase` is a CC its coordinants will be raised to VPs

    """
    element = raise_to_element(element)
    if isinstance(element, Coordination):
        element.coords = ElementList([raise_to_vp(c) for c in element.coords])
        return element
    if isinstance(element, String):
        return VerbPhrase(head=element)
    if isinstance(element, Word):
        return VerbPhrase(head=element)
    return element


def raise_to_phrase(element):
    """ Convert element into a phrase. If it is a clause, return it as is.

    We use `isinstance()` instead of the element category because functions,
    unlike classes can't be easily extended if you add a new category.

    """
    if is_clause_type(element):
        return element
    if is_phrase_type(element):
        return element
    if isinstance(element, (Var, String)):
        return NounPhrase(element, features=element.features)
    if isinstance(element, Word):
        if element.pos == category.VERB:
            return VerbPhrase(element, features=element.features)
        elif element.pos == category.ADVERB:
            return VerbPhrase(element, features=element.features)
        else:
            return NounPhrase(element, features=element.features)
    if isinstance(element, Coordination):
        element.coords = ElementList([raise_to_phrase(c) for c in element.coords])
        return element
    return NounPhrase(element, features=element.features)


def raise_to_clause(element):
    """ Convert element into a clause. If it is a clause, return it as is. """
    if is_clause_type(element):
        return element
    if is_phrase_type(element):
        if is_noun_type(element): return Clause(subject=element)
        if is_verb_type(element): return Clause(predicate=element)
    if isinstance(element, Coordination):
        element.coords = ElementList([raise_to_clause(c) for c in element.coords])
        return element
    return Clause(element)


def comparable_features(original_features):
    """Return a copy of features limited to ones that can be used
    for equality comparison.

    """
    rv = original_features.copy()
    # disregard DISCOURSE_FUNCTION features
    for f in NON_COMPARABLE_FEATURES:
        rv.discard(f)
    return rv


def transfer_features(source, target):
    """Copy transferable features from `source` to `target`."""
    if target is None:
        return
    for f in TRANSFERABLE_FEATURES:
        if f in source:
            target[f] = source[f]


class ElementEncoder(json.JSONEncoder):
    def default(self, python_object):
        if isinstance(python_object, (Element, ElementList)):
            dct = python_object.__dict__
            if 'parent' in dct:
                dct['parent'] = None
            return {'__class__': str(type(python_object)),
                    '__value__': dct}
        elif isinstance(python_object, FeatureSet):
            return {'__class__': str(type(python_object)),
                    '__value__': python_object.as_dict()}
        return super(ElementEncoder, self).default(python_object)


class ElementDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        kwargs['object_hook'] = ElementDecoder.from_json
        super(ElementDecoder, self).__init__(*args, **kwargs)

    @staticmethod
    def from_json(json_object):
        prefix = "<class 'nlglib.microplanning.struct."
        if '__class__' in json_object:
            cls = json_object['__class__']
            if cls == ("%sElement'>" % prefix):
                rv = Element.from_dict(json_object['__value__'])
            elif cls == ("%sElementList'>" % prefix):
                rv = ElementList.from_dict(json_object['__value__'])
            elif cls == ("%sString'>" % prefix):
                rv = String.from_dict(json_object['__value__'])
            elif cls == ("%sWord'>" % prefix):
                rv = Word.from_dict(json_object['__value__'])
            elif cls == ("%sVar'>" % prefix):
                rv = Var.from_dict(json_object['__value__'])
            elif cls == ("%sPhrase'>" % prefix):
                rv = Phrase.from_dict(json_object['__value__'])
            elif cls == ("%sNounPhrase'>" % prefix):
                rv = NounPhrase.from_dict(json_object['__value__'])
            elif cls == ("%sVerbPhrase'>" % prefix):
                rv = VerbPhrase.from_dict(json_object['__value__'])
            elif cls == ("%sPrepositionPhrase'>" % prefix):
                rv = PrepositionPhrase.from_dict(json_object['__value__'])
            elif cls == ("%sAdjectivePhrase'>" % prefix):
                rv = AdjectivePhrase.from_dict(json_object['__value__'])
            elif cls == ("%sAdverbPhrase'>" % prefix):
                rv = AdverbPhrase.from_dict(json_object['__value__'])
            elif cls == ("%sCoordination'>" % prefix):
                rv = Coordination.from_dict(json_object['__value__'])
            elif cls == ("%sClause'>" % prefix):
                rv = Clause.from_dict(json_object['__value__'])
            elif cls == "<class 'nlglib.features.feature.FeatureSet'>":
                rv = FeatureSet()
                rv.update(json_object['__value__'])
            else:
                raise TypeError('Unknown class "{}"'.format(cls))
            if hasattr(rv, 'update_parents'):
                rv.update_parents()
            return rv
        return json_object
