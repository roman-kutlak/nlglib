"""Data structures used by other packages. """

# FIXME: more unit tests with coverage
# TODO: check serialisation of phrases/clause
# TODO: check deepcopy
# TODO: raise_to_xxx should use category
# TODO: set discourse features of elements \
# (matrix clause, object, subject, head, spec, ...)
# TODO: create module `element_algebra` and pud add/iadd into it
# TODO: move current microplanning visitors into \
# mod microplanning.visitors or struct.visitors
# TODO: remove 'subj' and 'vp' from clause?


import collections
import inspect
import importlib
import json
import logging
import os

from copy import deepcopy
from os.path import join, dirname, relpath
from urllib.parse import quote_plus

from nlglib.features import discourse

logger = logging.getLogger(__name__)

_sentinel = object()

# types of clauses:
ELEMENT_LIST = 'ELEMENT_LIST'
ELEMENT = 'ELEMENT'  # abstract
VAR = 'VAR'
STRING = 'STRING'
WORD = 'WORD'

#  A default value, indicating an unspecified category.
ANY = "ANY"
#  The element represents a symbol.
SYMBOL = "SYMBOL"

NOUN = "NOUN"
ADJECTIVE = "ADJECTIVE"
ADVERB = "ADVERB"
VERB = "VERB"
DETERMINER = "DETERMINER"
PRONOUN = "PRONOUN"
CONJUNCTION = "CONJUNCTION"
PREPOSITION = "PREPOSITION"
COMPLEMENTISER = "COMPLEMENTISER"
MODAL = "MODAL"
AUXILIARY = "AUXILIARY"

PHRASE = 'PHRASE'  # abstract
NOUN_PHRASE = 'NOUN_PHRASE'
VERB_PHRASE = 'VERB_PHRASE'
PREPOSITION_PHRASE = 'PREPOSITION_PHRASE'
ADJECTIVE_PHRASE = 'ADJECTIVE_PHRASE'
ADVERB_PHRASE = 'ADVERB_PHRASE'

CLAUSE = 'CLAUSE'
COORDINATION = 'COORDINATION'

CATEGORIES = [
    ELEMENT, STRING, WORD, VAR,
    COORDINATION,
    PHRASE, NOUN_PHRASE, VERB_PHRASE,
    PREPOSITION_PHRASE, ADJECTIVE_PHRASE, ADVERB_PHRASE,
    CLAUSE
]

# features that are excluded from equality comparison
NON_COMPARABLE_FEATURES = [discourse.FEATURE_GROUP]

# features that should be transferred on replacement
TRANSFERABLE_FEATURES = [discourse.FEATURE_GROUP]


class FeatureModulesLoader(type):
    """Metaclass injecting the feature module property onto a class."""

    def __new__(cls, clsname, bases, dct):
        features = {}
        feature_pkg_path = relpath(
            join(dirname(__file__), '..', 'lexicon', 'feature'))
        for dirpath, _, filenames in os.walk(feature_pkg_path):
            pkg_root = dirpath.replace('/', '.')
            for filename in filenames:
                if not filename.endswith('.py'):
                    continue
                pkg_path = pkg_root + '.' + filename.replace('.py', '')
                if pkg_path.startswith('.'):  # no relative imports please
                    _, root, child = pkg_path.rpartition('nlglib')
                    pkg_path = root + child
                mod = importlib.import_module(pkg_path)
                modfeatures = [c for c in dir(mod) if c.isupper()]
                for feat in modfeatures:
                    features[feat] = getattr(mod, feat)

        dct['_feature_constants'] = features

        return super(FeatureModulesLoader, cls).__new__(
            cls, clsname, bases, dct)


class Element(object, metaclass=FeatureModulesLoader):
    """A base class representing an NLG element.
        Aside for providing a base class for other kinds of NLG elements,
        the class also implements basic functionality for elements.

    """

    category = ELEMENT

    def __init__(self, features=None, parent=None, id=None):
        self.features = features or {}
        self.parent = parent
        self.id = id
        self.hash = -1
        if 'cat' not in self.features:
            self.features['cat'] = 'ANY'

    def __copy__(self):
        rv = self.__class__(features=self.features,
                            parent=self.parent,
                            id=self.id)
        return rv

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

    def __repr__(self):
        from nlglib.microplanning import ReprVisitor
        v = ReprVisitor()
        self.accept(v)
        return str(v)

    def __str__(self):
        from nlglib.microplanning import StrVisitor, SimpleStrVisitor
        v = SimpleStrVisitor()
        self.accept(v)
        return str(v)

    def __contains__(self, feature_name):
        """Check if the argument feature name is contained in the element."""
        return feature_name in self.features

    def __setitem__(self, feature_name, feature_value):
        """Set the feature name/value in the element feature dict."""
        self.features[feature_name] = feature_value

    def __getitem__(self, feature_name):
        """Return the value associated with the feature name, from the
        element feature dict.

        If the feature name is not found in the feature dict, return None.

        """
        return self.features.get(feature_name)

    def __delitem__(self, feature_name):
        """Remove the argument feature name and its associated value from
        the element feature dict.

        If the feature name was not initially present in the feature dict,
        a KeyError will be raised.

        """
        if feature_name in self.features:
            del self.features[feature_name]

    def __getattr__(self, name):
        """When a undefined attribute name is accessed, try to return
        self.features[name] if it exists.

        If name is not in self.features, but name.upper() is defined as
        a feature constant, don't raise an AttribueError. Instead, try
        to return the feature value associated with the feature constant
        value.

        This allows us to have a more consistant API when
        dealing with NLGElement and instances of sublclasses.

        If no such match is found, raise an AttributeError.

        Example:
        >>> elt = Element(features={'plural': 'plop', 'infl': ['foo']})
        >>> elt.plural
        'plop'  # because 'plural' is in features
        >>> elt.infl
        ['foo']  # because 'infl' is in features
        >>> elt.inflections
        ['foo']  # because INFLECTIONS='infl' is defined as a feature constant
                # constant, and elt.features['infl'] = ['foo']

        """
        n = name.upper()
        if name in self.features:
            return self.features[name]
        elif n in self._feature_constants:
            new_name = self._feature_constants[n]
            return self.features.get(new_name)
        cls_name = self.__class__.__name__
        raise AttributeError('{} does not have attribute {}'.format(cls_name, name))

    def __add__(self, other):
        """Add two elements resulting in a coordination 
        if both elements are not "False" else return the "True" element.
        
        """
        if not self:
            return other
        if not other:
            return self
        return Coordination(self, other)

    def to_str(self):
        from nlglib.microplanning import SimpleStrVisitor
        visitor = SimpleStrVisitor()
        self.accept(visitor)
        return str(visitor)

    def to_xml(self, depth=0, headers=False):
        from nlglib.microplanning import XmlVisitor
        visitor = XmlVisitor(depth=depth)
        self.accept(visitor)
        if headers:
            return str(visitor)
        else:
            return str(visitor.xml)

    def accept(self, visitor, element='Element'):
        """Implementation of the Visitor pattern."""
        visitor_name = 'visit_' + self.category.lower()
        # get the appropriate method of the visitor instance
        m = getattr(visitor, visitor_name)
        # ensure that the method is callable
        if not hasattr(m, '__call__'):
            msg = 'Error: cannot call undefined method: %s on visitor'
            raise ValueError(msg % visitor_name)
        sig = inspect.signature(m)
        # and finally call the callback
        if len(sig.parameters) == 1:
            return m(self)
        if len(sig.parameters) == 2:
            return m(self, element)

    def features_to_xml_attributes(self):
        features = ""
        keys = sorted(self.features.keys())
        for k in keys:
            v = str(self.features[k])
            if v.lower() in ('true', 'false'):
                v = v.lower()
            elif k not in ('conj', 'COMPLEMENTISER'):
                v = v.upper()
            features += '%s="%s" ' % (quote_plus(str(k)), quote_plus(str(v)))
        features = features.strip()
        if features != '':
            return ' ' + features
        return ''

    def constituents(self):
        """Return a list or a generator representing 
        the constituents of an element. 
        
        """
        return []

    def arguments(self):
        """Return any arguments (vars) from the element as a list. """
        return [x for x in self.constituents() if x.category == VAR]

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

    def has_feature(self, feature, value=None):
        import warnings
        warnings.warn('This method is deprecated')
        if not value:
            return feature in self
        else:
            return self[feature] == value

    def get_feature(self, feature, value=None):
        import warnings
        warnings.warn('This method is deprecated')
        if feature not in self:
            return value
        else:
            return self[feature]

    def set_feature(self, feature, value=None):
        import warnings
        warnings.warn('This method is deprecated')
        self[feature] = value


class ElementList(collections.UserList):
    category = ELEMENT_LIST

    def __init__(self, lst=None, parent=None, features=None):
        super().__init__()
        self.parent = parent
        self.features = features or {}
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

    def __iadd__(self, other):
        if isinstance(other, (ElementList, list, tuple)):
            for x in other:
                self.append(x)
        else:
            self.append(other)
        return self

    def __setitem__(self, i, value):
        value = raise_to_element(value)
        # FIXME: is this a bug? missing parent and features
        # value.parent = self.parent
        # value.features.update(self.features)
        super().__setitem__(i, value)

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

    def constituents(self):
        return iter(self)

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

    category = VAR

    def __init__(self, id=None, obj=None, features=None, parent=None):
        super().__init__(features, parent, id)
        self.value = None
        self.set_value(obj)
        self.features['cat'] = 'ANY'

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

    def __deepcopy__(self, memo):
        rv = self.__class__(self.id, self.value)
        memo[id(self)] = rv
        rv.features = deepcopy(self.features, memo=memo)
        rv.parent = memo.get(id(self.parent), None)
        return rv

    def constituents(self):
        return [self]

    def set_value(self, val):
        if val is None: val = Word(str(self.id), 'NOUN')
        self.value = String(val) if isinstance(val, str) else val

    @property
    def string(self):
        """Return the string inside the value. """
        return self.value.string


class String(Element):
    """String is a basic element representing canned text. """

    category = STRING

    def __init__(self, value='', features=None, parent=None, id=None):
        super().__init__(features, parent, id)
        self.value = str(value)
        self.features['cat'] = 'ANY'

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

    def __deepcopy__(self, memo):
        rv = self.__class__(self.value, None, None, self.id)
        memo[id(self)] = rv
        rv.features = deepcopy(self.features, memo=memo)
        rv.parent = memo.get(id(self.parent), None)
        return rv

    def constituents(self):
        return [self]

    @property
    def string(self):
        """Return the string inside the value. """
        return self.value


class Word(Element):
    """Word represents word and its corresponding POS (Part-of-Speech) tag. """

    category = WORD

    def __init__(self, word, pos='ANY', features=None, parent=None, id=None):
        super().__init__(features, parent, id)
        self.word = str(word)
        self.pos = pos
        self.features['cat'] = pos
        self.do_inflection = False

    def __bool__(self):
        """Return True """
        return True

    def __eq__(self, other):
        return super().__eq__(other) and self.word == other.word

    def __hash__(self):
        if self.hash == -1:
            self.hash = hash(str(self))
        return self.hash

    def __copy__(self):
        # pos is in features
        return self.__class__(self.word, pos=self.pos, features=self.features,
                              parent=self.parent, id=self.id)

    def __deepcopy__(self, memo):
        # pos is in features
        rv = self.__class__(self.word, pos=self.pos, features=None,
                            parent=None, id=self.id)
        memo[id(self)] = rv
        rv.features = deepcopy(self.features, memo=memo)
        rv.parent = memo.get(id(self.parent), None)
        return rv

    def constituents(self):
        return [self]

    @property
    def string(self):
        """Return the word. """
        return self.word


class Coordination(Element):
    """Coordinated clause with a conjunction. 
    
    The class enforces that the coordinates are of the same type.
    
    """

    category = COORDINATION

    def __init__(self, *coords, conj='and', features=None, parent=None, id=None):
        super().__init__(features, parent, id)
        self.coords = ElementList(parent=self)
        self.add_coordinates(*coords)
        self.coordinate_category = self.coords[0].cat if self.coords else None
        self.features['conj'] = conj

    def __len__(self):
        return len(self.coords)

    def __eq__(self, other):
        return super().__eq__(other) and self.coords == other.coords

    def __hash__(self):
        if self.hash == -1:
            self.hash = hash(str(self))
        return self.hash

    def __copy__(self):
        return self.__class__(*self.coords, features=self.features,
                              parent=self.parent, id=self.id)

    def __deepcopy__(self, memo):
        # pos is in features
        rv = self.__class__(features=None, parent=None, id=self.id)
        memo[id(self)] = rv
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
        other.features.pop('discourseFunction', None)
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
            if x.category == COORDINATION:
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
            cat = self.coords[0].cat
            if not all(x.coordinate_category == cat if isinstance(x, Coordination) else x.cat == cat for x in self.coords):
                msg = ('All elements of a coordination have to have '
                       'the same lexical category ({} but entering {}).')
                raise TypeError(msg.format(cat, self.coords[-1].cat))

    def constituents(self):
        """Return a generator to iterate through constituents. """
        yield self
        for c in self.coords:
            yield c
            if hasattr(c, 'constituents'):
                yield from c.constituents()

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
    category = PHRASE

    def __init__(self, features=None, parent=None, id=None, **kwargs):
        super().__init__(features, parent, id)
        self['cat'] = self.category
        self.premodifiers = (ElementList(parent=self) +
                             kwargs.pop('premodifiers', []))
        self.head = kwargs.pop('head', None)
        self.complements = (ElementList(parent=self) +
                            kwargs.pop('complements', []))
        self.postmodifiers = (ElementList(parent=self) +
                              kwargs.pop('postmodifiers', []))

    def __bool__(self):
        """Return True """
        return any([x for x in self.constituents() if x is not self])

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
        if is_adj_mod_t(other) or is_adv_mod_t(other):
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
        self._head[discourse.FEATURE_GROUP] = discourse.HEAD

    def yield_premodifiers(self):
        """Iterate through pre-modifiers. """
        for o in self.premodifiers:
            for x in o.constituents():
                yield from x.constituents()

    def yield_head(self):
        """Iterate through the elements composing the head. """
        if self.head is not None:
            for x in self.head.constituents():
                yield from x.constituents()

    def yield_complements(self):
        """Iterate through complements. """
        for o in self.complements:
            for x in o.constituents():
                yield from x.constituents()

    def yield_postmodifiers(self):
        """Iterate throught post-modifiers. """
        for o in self.postmodifiers:
            for x in o.constituents():
                yield from x.constituents()

    def constituents(self):
        """Return a generator to iterate through constituents. """
        yield self
        yield from self.yield_premodifiers()
        yield from self.yield_head()
        yield from self.yield_complements()
        yield from self.yield_postmodifiers()

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
            self.features['cat'] = self.category
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
     * <UL>
     * <li>Specifier     (eg, "the")</LI>
     * <LI>PreModifier   (eg, "green")</LI>
     * <LI>Noun (head)   (eg, "apples")</LI>
     * <LI>complement    (eg, "that you liked")</LI>
     * <LI>PostModifier  (eg, "in the shop")</LI>
     * </UL>
     """

    _spec = Element()
    category = NOUN_PHRASE

    def __init__(self, head=None, spec=None, features=None,
                 parent=None, id=None, **kwargs):
        super().__init__(features, parent, id, **kwargs)
        self.spec = spec
        self.head = head

    def __eq__(self, other):
        return (super().__eq__(other) and
                self.spec == other.spec and
                self.head == other.head)

    def __hash__(self):
        if self.hash == -1:
            self.hash = hash(str(self))
        return self.hash

    def __copy__(self):
        rv = self.__class__(self.head, self.spec, features=self.features,
                            parent=self.parent, id=self.id)
        rv.premodifiers = self.premodifiers[:]
        rv.complements = self.complements[:]
        rv.postmodifiers = self.postmodifiers[:]
        return rv

    def __deepcopy__(self, memo):
        rv = super().__deepcopy__(memo=memo)
        rv.spec = deepcopy(self.spec, memo=memo)
        return rv

    @property
    def spec(self):
        return self.specifier

    @spec.setter
    def spec(self, value):
        self.specifier = value

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
        self._spec[discourse.FEATURE_GROUP] = discourse.SPECIFIER

    def constituents(self):
        """Return a generator to iterate through constituents. """
        yield self
        for c in self.spec.constituents():
            yield from c.constituents()
        yield from self.yield_premodifiers()
        yield from self.yield_head()
        yield from self.yield_complements()
        yield from self.yield_postmodifiers()

    def replace(self, one, another, key=lambda x: x):
        """Replace first occurrence of one with another.
        Return True if successful.

        """
        one = raise_to_element(one)
        another = raise_to_element(another)

        if key(self.spec) == key(one):
            self.spec.parent = None
            another.parent = self
            transfer_features(self.spec, another)
            self.spec = another
            return True
        if self.spec.replace(one, another, key):
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
    * <UL>
     * <LI>PreModifier      (eg, "reluctantly")</LI>
     * <LI>Verb             (eg, "gave")</LI>
     * <LI>IndirectObject   (eg, "Mary")</LI>
     * <LI>Object           (eg, "an apple")</LI>
     * <LI>PostModifier     (eg, "before school")</LI>
     * </UL>
     """

    category = VERB_PHRASE

    def __init__(self, head=None, *compl, features=None, parent=None, **kwargs):
        super().__init__(features, parent, **kwargs)
        self.head = head
        self.complements += compl
        if 'object' in kwargs:
            self.object = kwargs.pop('object')
        if 'direct_object' in kwargs:
            self.object = kwargs.pop('direct_object')
        if 'indirect_object' in kwargs:
            self.indirect_object = kwargs.pop('indirect_object')

    @property
    def object(self):
        for c in self.complements:
            if c[discourse.FEATURE_GROUP] == discourse.OBJECT:
                return c
        return None

    @object.setter
    def object(self, value):
        to_remove = [c for c in self.complements
                     if c[discourse.FEATURE_GROUP] == discourse.OBJECT]
        for c in to_remove:
            self.complements.remove(c)
        if value is None:
            return
        new_value = raise_to_element(value)
        new_value.parent = self
        new_value[discourse.FEATURE_GROUP] = discourse.OBJECT
        self.complements.append(new_value)

    @property
    def direct_object(self):
        return self.object

    @direct_object.setter
    def direct_object(self, value):
        self.object = value

    @property
    def indirect_object(self):
        for c in self.complements:
            if c[discourse.FEATURE_GROUP] == discourse.INDIRECT_OBJECT:
                return c
        return None

    @indirect_object.setter
    def indirect_object(self, value):
        to_remove = [c for c in self.complements
                     if c[discourse.FEATURE_GROUP] == discourse.INDIRECT_OBJECT]
        for c in to_remove:
            self.complements.remove(c)
        if value is None:
            return
        new_value = raise_to_element(value)
        new_value.parent = self
        new_value[discourse.FEATURE_GROUP] = discourse.INDIRECT_OBJECT
        self.complements.insert(0, new_value)


class PrepositionPhrase(Phrase):
    category = PREPOSITION_PHRASE

    def __init__(self, head=None, *compl, features=None, parent=None, **kwargs):
        super().__init__(features, parent, **kwargs)
        self.head = head
        self.complements += compl


class AdverbPhrase(Phrase):
    category = ADVERB_PHRASE

    def __init__(self, head=None, *compl, features=None, parent=None, **kwargs):
        super().__init__(features, parent, **kwargs)
        self.head = head
        self.complements += compl


class AdjectivePhrase(Phrase):
    category = ADJECTIVE_PHRASE

    def __init__(self, head=None, *compl, features=None, parent=None, **kwargs):
        super().__init__(features, parent, **kwargs)
        self.head = head
        self.complements += compl


class Clause(Phrase):
    """Clause - sentence.
    From simplenlg:
 * <UL>
 * <li>FrontModifier (eg, "Yesterday")
 * <LI>Subject (eg, "John")
 * <LI>PreModifier (eg, "reluctantly")
 * <LI>Verb (eg, "gave")
 * <LI>IndirectObject (eg, "Mary")
 * <LI>Object (eg, "an apple")
 * <LI>PostModifier (eg, "before school")
 * </UL>
 * Note that verb, indirect object, and object are propagated to the underlying
 * verb phrase

    """

    _subject = None
    _predicate = None
    category = CLAUSE

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
        if is_adj_mod_t(other):
            self_.subj += other_
            return self_
        if is_adv_mod_t(other):
            self_.vp += other_
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
        return self.subj.string if self.subj else self.predicate.string

    @property
    def subject(self):
        return self._subject

    @subject.setter
    def subject(self, value):
        if self._subject:
            self._subject.parent = None
        if value is not None:
            new_value = raise_to_np(value)
            new_value.parent = self
            self._subject = new_value
        else:
            self._subject = Element()
        self._subject[discourse.FEATURE_GROUP] = discourse.SUBJECT

    @property
    def subj(self):
        return self.subject

    @subj.setter
    def subj(self, value):
        self.subject = value

    @property
    def predicate(self):
        return self._predicate

    @predicate.setter
    def predicate(self, value):
        if self._predicate:
            self._predicate.parent = None
        if value is not None:
            new_value = raise_to_vp(value)
            new_value.parent = self
            self._predicate = new_value
        else:
            self._predicate = Element()
        self._predicate[discourse.FEATURE_GROUP] = discourse.PREDICATE

    @property
    def head(self):
        return self.predicate

    @head.setter
    def head(self, value):
        self.predicate = value

    @property
    def vp(self):
        return self.predicate

    @vp.setter
    def vp(self, value):
        self.predicate = value

    @property
    def verb(self):
        return self.predicate.head if self.predicate else None

    @verb.setter
    def verb(self, value):
        if self.predicate:
            self.predicate.head = raise_to_element(value)
        else:
            self.predicate = value

    @property
    def object(self):
        return self.predicate.object if self.predicate else None

    @object.setter
    def object(self, value):
        if self.predicate:
            self.predicate.object = value
        else:
            msg = "Clause doesn't have a verb to set its object."
            raise KeyError(msg)

    @property
    def indirect_object(self):
        return self.predicate.indirect_object if self.predicate else None

    @indirect_object.setter
    def indirect_object(self, value):
        if self.predicate:
            self.predicate.indirect_object = value
        else:
            msg = "Clause doesn't have a verb to set its indirect object."
            raise KeyError(msg)

    def constituents(self):
        """Return a generator to iterate through constituents. """
        yield self
        yield from self.yield_front_modifiers()
        yield from self.subject.constituents()
        yield from self.yield_premodifiers()
        yield from self.predicate.constituents()
        yield from self.yield_complements()
        yield from self.yield_postmodifiers()

    def replace(self, one, another, key=lambda x: x):
        """Replace first occurance of one with another.
        Return True if successful.

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

    def yield_front_modifiers(self):
        """Iterate through front-modifiers. """
        for o in self.front_modifiers:
            for x in o.constituents():
                yield from x.constituents()

    def update_parents(self, parent=_sentinel):
        if parent is not _sentinel:
            self.parent = parent
        new_parent = None if parent is None else self
        to_update = [self.front_modifiers, self.subject, self.predicate]
        for x in to_update:
            x.update_parents(new_parent)
        super().update_parents(parent)


def raise_to_element(element):
    """Raise the given thing to an element (e.g., String). """
    if element is None:
        return Element()
    if not isinstance(element, Element):
        return String(str(element))  # use str() in case of numbers
    return element


def raise_to_np(phrase):
    """Take the current phrase and raise it to an NP.
    If `phrase` is a Noun it will be promoted to NP and used as a head;
    If `phrase` is a CC its coordinates will be raised to NPs

    """
    phrase = raise_to_element(phrase)
    if isinstance(phrase, Coordination):
        phrase.coords = [raise_to_np(c) for c in phrase.coords]
        return phrase
    if isinstance(phrase, (String, Word)):
        return NounPhrase(head=phrase)
    if isinstance(phrase, Element) and phrase.category == ELEMENT:
        return NounPhrase(head=phrase)
    return phrase


def raise_to_vp(phrase):
    """Take the current phrase and raise it to a VP.
    If `phrase` is a Word it will be promoted to VP and used as a head;
    If `phrase` is a CC its coordinants will be raised to VPs

    """
    phrase = raise_to_element(phrase)
    if isinstance(phrase, Coordination):
        phrase.coords = [raise_to_vp(c) for c in phrase.coords]
        return phrase
    if isinstance(phrase, String):
        return VerbPhrase(head=phrase)
    if isinstance(phrase, Word):
        return VerbPhrase(head=phrase)
    return phrase


def is_element_t(o):
    """Return True if `o` is an instance of `Element`."""
    return isinstance(o, Element)


def is_phrase_t(o):
    """Return True if `o` is a phrase. """
    return (is_element_t(o) and
            (o.category in (PHRASE, NOUN_PHRASE, VERB_PHRASE,
                            ADJECTIVE_PHRASE, ADVERB_PHRASE,
                            PREPOSITION_PHRASE)))


def is_clause_t(o):
    """An object is a clause type if it is a clause, subordination or
    a coordination of clauses.

    """
    return is_element_t(o) and o.category == CLAUSE


def is_adj_mod_t(o):
    """Return True if `o` is adjective modifier (adj or AdjP)"""
    from nlglib import lexicon
    return (isinstance(o, AdjectivePhrase) or
            isinstance(o, Word) and o.pos == ADJECTIVE or
            isinstance(o, Coordination) and is_adj_mod_t(o.coords[0]))


def is_adv_mod_t(o):
    """Return True if `o` is adverb modifier (adv or AdvP)"""
    from nlglib import lexicon
    return (isinstance(o, AdverbPhrase) or
            isinstance(o, Word) and o.pos == ADVERB or
            isinstance(o, Coordination) and is_adv_mod_t(o.coords[0]))


def is_noun_t(o):
    """Return True if `o` is adverb modifier (adv or AdvP)"""
    from nlglib import lexicon
    return (isinstance(o, NounPhrase) or
            isinstance(o, Word) and o.pos == NOUN or
            isinstance(o, Coordination) and is_noun_t(o.coords[0]))


def comparable_features(features):
    """Return a dict of features limited to ones that can be used 
    for equality comparison.
    
    """
    rv = features.copy()
    # disregard discourse features
    ignored = NON_COMPARABLE_FEATURES
    for f in ignored:
        rv.pop(f, None)
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
        dct = python_object.__dict__
        if 'parent' in dct:
            dct['parent'] = None
        if isinstance(python_object, (Element, ElementList)):
            return {'__class__': str(type(python_object)),
                    '__value__': dct}
        return super(ElementEncoder, self).default(python_object)


class ElementDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        kwargs['object_hook'] = ElementDecoder.from_json
        super(ElementDecoder, self).__init__(*args, **kwargs)

    @staticmethod
    def from_json(json_object):
        prefix = "<class 'nlglib.structures.microplanning."
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
            else:
                raise TypeError('Unknown class "{}"'.format(cls))
            rv.update_parents()
            return rv
        return json_object
