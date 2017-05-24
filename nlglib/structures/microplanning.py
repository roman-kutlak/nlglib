""" Data structures used by other packages. """

import inspect
import importlib
import json
import logging
import os

from copy import deepcopy
from os.path import join, dirname, relpath
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)

# types of clauses:
ELEMENT = 0  # abstract
STRING = 1
WORD = 2
VAR = 3
CLAUSE = 4

COORDINATION = 5
SUBORDINATION = 6

PHRASE = 10  # abstract
NOUN_PHRASE = 11
VERB_PHRASE = 12
PREPOSITIONAL_PHRASE = 13
ADJECTIVE_PHRASE = 14
ADVERB_PHRASE = 15

# visitor names
VisitorNames = {
    ELEMENT: 'visit_element',
    STRING: 'visit_string',
    WORD: 'visit_word',
    VAR: 'visit_var',
    CLAUSE: 'visit_clause',

    COORDINATION: 'visit_coordination',

    PHRASE: 'visit_phrase',
    NOUN_PHRASE: 'visit_np',
    VERB_PHRASE: 'visit_vp',
    PREPOSITIONAL_PHRASE: 'visit_pp',
    ADJECTIVE_PHRASE: 'visit_adjp',
    ADVERB_PHRASE: 'visit_advp',
}


def is_element_t(o):
    """ An object is an element if it has attr type and one of the types. """
    if not hasattr(o, 'type'):
        return False
    else:
        return o.type in VisitorNames


def is_phrase_t(o):
    """ An object is a phrase type if it is a phrase or a coordination of
    phrases.

    """
    return (is_element_t(o) and
            (o.type in {PHRASE, NounPhrase, VerbPhrase, PrepositionalPhrase,
                        ADJECTIVE_PHRASE, ADVERB_PHRASE} or
             (o.type == COORDINATION and
              (o.coords == [] or is_phrase_t(o.coords[0])))))


def is_clause_t(o):
    """ An object is a clause type if it is a clause, subordination or
    a coordination of clauses.

    """
    return (is_element_t(o) and
            ((o.type in {CLAUSE, SUBORDINATION}) or
             (o.type == COORDINATION and any(map(is_clause_t, o.coords)))))


def is_adj_mod_t(o):
    """Return True if `o` is adjective modifier (adj or AdjP)"""
    from nlglib import lexicon
    return (isinstance(o, AdjectivePhrase) or
            isinstance(o, Word) and o.pos == lexicon.POS_ADJECTIVE or
            isinstance(o, Coordination) and is_adj_mod_t(o.coords[0]))


def is_adv_mod_t(o):
    """Return True if `o` is adverb modifier (adv or AdvP)"""
    from nlglib import lexicon
    return (isinstance(o, AdverbPhrase) or
            isinstance(o, Word) and o.pos == lexicon.POS_ADVERB or
            isinstance(o, Coordination) and is_adv_mod_t(o.coords[0]))


def is_noun_t(o):
    """Return True if `o` is adverb modifier (adv or AdvP)"""
    from nlglib import lexicon
    return (isinstance(o, NounPhrase) or
            isinstance(o, Word) and o.pos == lexicon.POS_NOUN or
            isinstance(o, Coordination) and is_noun_t(o.coords[0]))


def str_to_elt(*params):
    """ Check that all params are Elements and convert
    and any strings to String.

    """
    def helper(x):
        return String(x) if isinstance(x, str) else x
    return list(map(helper, params))


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
                    _, root, child = pkg_path.rpartition('pynlg')
                    pkg_path = root + child
                mod = importlib.import_module(pkg_path)
                modfeatures = [c for c in dir(mod) if c.isupper()]
                for feat in modfeatures:
                    features[feat] = getattr(mod, feat)

        dct['_feature_constants'] = features

        return super(FeatureModulesLoader, cls).__new__(
            cls, clsname, bases, dct)


class Element(object, metaclass=FeatureModulesLoader):
    """ A base class representing an NLG element.
        Aside for providing a base class for other kinds of NLG elements,
        the class also implements basic functionality for elements.

    """

    def __init__(self, type=ELEMENT, features=None, parent=None):
        if features and not isinstance(features, dict):
            raise ValueError('Features have to be a dict instance.')
        self.id = 0  # this is useful for replacing elements
        self.type = type
        self._visitor_name = VisitorNames[type]
        self.features = deepcopy(features) if features else {}
        self.hash = -1
        self.parent = parent

    def __bool__(self):
        """ Because Element is abstract, it will evaluate to false. """
        return False

    def __eq__(self, other):
        if not is_element_t(other): return False
        if self.type is not other.type: return False
        return (self.id == other.id and
                self.features == other.features)

    def __hash__(self):
        if self.hash == -1:
            self.hash = (hash(self.id) ^ hash(tuple(['k:v'.format(k, v)
                                                     for k, v in
                                                     self.features.items()])))
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
        from nlglib.microplanning import StrVisitor
        v = StrVisitor()
        self.accept(v)
        return str(v)

    # feature-related methods
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
        >>> elt = NLGElement(features={'plural': 'plop', 'infl': ['foo']})
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
        raise AttributeError(name)

    def __deepcopy__(self, memodict=None):
        copyobj = self.__class__(self.type, self.features, self.parent)
        copyobj.id = self.id
        copyobj.hash = self.hash
        return copyobj

    def to_str(self):
        from nlglib.microplanning import SimpleStrVisitor
        visitor = SimpleStrVisitor()
        self.accept(visitor)
        return str(visitor)

    def to_xml(self, depth=0):
        from nlglib.microplanning import XmlVisitor
        visitor = XmlVisitor(depth=depth)
        self.accept(visitor)
        return str(visitor.xml)

    def accept(self, visitor, element='Element'):
        """Implementation of the Visitor pattern."""
        if self._visitor_name is None:
            raise ValueError('Error: visit method of uninitialized visitor called!')
        # get the appropriate method of the visitor instance
        m = getattr(visitor, self._visitor_name)
        # ensure that the method is callable
        if not hasattr(m, '__call__'):
            raise ValueError('Error: cannot call undefined method: %s on visitor'
                             % self._visitor_name)
        sig = inspect.signature(m)
        # and finally call the callback
        if len(sig.parameters) == 1:
            return m(self)
        if len(sig.parameters) == 2:
            return m(self, element)

    def features_to_xml_attributes(self):
        features = ""
        for (k, v) in self.features.items():
            features += '%s="%s" ' % (quote_plus(str(k)), quote_plus(str(v)))
        features = features.strip()
        if features != '':
            return ' ' + features
        return ''

    def constituents(self):
        """ Return a generator representing constituents of an element. """
        return []

    def arguments(self):
        """ Return any arguments (vars) from the elemen as a generator.

        """
        return list(filter(lambda x: isinstance(x, Var),
                           self.constituents()))

    def replace(self, one, another):
        """ Replace first occurrence of one with another.
        Return True if successful.

        """
        return False  # basic implementation does nothing

    def replace_argument(self, arg_id, replacement):
        """ Replace an argument with given id by `replacement` if such argument exists."""
        for a in self.arguments():
            if a.id == arg_id:
                return self.replace(a, replacement)
        return False

    def replace_arguments(self, *args, **kwargs):
        """ Replace arguments with ids in the kwargs by the corresponding values.
        
        Replacements can be passed as a single dictionary or a kwarg list
        (e.g., arg1=x, arg2=y, ...)

        """
        # FIXME: this does not look correct...
        if len(args) > 1:
            raise ValueError('too many parameters')
        elif len(args) > 0:
            for k, v in args[0]:
                self.replace_argument(k, v)
        else:
            for k, v in kwargs.items():
                self.replace_argument(k, v)

    @property
    def string(self):
        """Return the string inside the value. """
        return None

    def _add_to_list(self, lst, *mods, pos=None):
        """ Add modifiers to the given list. Convert any strings to String. """
        if pos is None:
            for mod in mods:
                mod.parent = self
                lst.append(mod)
        else:
            for mod in mods:
                mod.parent = self
                lst.insert(pos, mod)

    @staticmethod
    def _del_from_list(lst, *mods):
        """ Delete elements from a list. Convert any strings to String. """
        for p in str_to_elt(*mods):
            if p in lst: lst.remove(p)


class String(Element):
    """ String is a basic element representing canned text. """

    def __init__(self, val='', features=None, parent=None):
        super().__init__(STRING, features, parent)
        self.value = val

    def __bool__(self):
        """ Return True if the string is non-empty. """
        return len(self.value) > 0

    def __eq__(self, other):
        if (not isinstance(other, String)):
            return False
        return (self.value == other.value and
                super().__eq__(other))

    def __hash__(self):
        if self.hash == -1:
            self.hash = (11 * super().__hash__()) ^ hash(self.value)
        return self.hash

    def __deepcopy__(self, memodict={}):
        copyobj = self.__class__(self.value, self.features, self.parent)
        copyobj.id = self.id
        copyobj.hash = self.hash
        return copyobj

    def constituents(self):
        return [self]

    @property
    def string(self):
        """Return the string inside the value. """
        return self.value


class Word(Element):
    """ Word represents word and its corresponding POS (Part-of-Speech) tag. """

    def __init__(self, word, pos='ANY', features=None, base=None, parent=None):
        super().__init__(WORD, features, parent)
        self.word = word
        self.pos = pos
        self.base = base or word
        self.do_inflection = False
        self.cat = pos

    def __bool__(self):
        """ Return True """
        return True

    def __eq__(self, other):
        if (not isinstance(other, Word)):
            return False
        return (self.word == other.word and
                self.pos == other.pos and
                super().__eq__(other))

    def __hash__(self):
        if self.hash == -1:
            self.hash = ((11 * super().__hash__()) ^
                         (hash(self.pos) ^ hash(self.word)))
        return self.hash

    def __deepcopy__(self, memodict={}):
        copyobj = self.__class__(self.word, self.pos,
                                 self.features, self.base, self.parent)
        copyobj.id = self.id
        copyobj.hash = self.hash
        return copyobj

    def constituents(self):
        return [self]

    @property
    def string(self):
        """Return the word. """
        return self.word


class Var(Element):
    """ An element used as a place-holder in a sentence. The purpose of this
        element is to make replacing arguments easier. For example, in a plan
        one might want to replace arguments of an action with the instantiated
        objects
        E.g.,   move (x, a, b) -->
                move Var(x) from Var(a) to Var(b) -->
                move (the block) from (the table) to (the green block)

    """

    def __init__(self, id=None, obj=None, features=None, parent=None):
        super().__init__(VAR, features, parent)
        self.id = id
        self.value = None
        self.set_value(obj)

    def __bool__(self):
        """ Return True """
        return True

    def __eq__(self, other):
        if not isinstance(other, Var):
            return False
        else:
            return (self.id == other.id and
                    self.value == other.value and
                    super().__eq__(other))

    def __hash__(self):
        if self.hash == -1:
            self.hash = ((11 * super().__hash__()) ^
                         (hash(self.id) & hash(self.value)))
        return self.hash

    def __deepcopy__(self, memodict={}):
        copyobj = self.__class__(self.id, self.value, features=self.features,
                                 parent=self.parent)
        copyobj.id = self.id
        copyobj.hash = self.hash
        return copyobj

    def constituents(self):
        return [self]

    def set_value(self, val):
        if val is None: val = Word(str(self.id), 'NOUN')
        self.value = String(val) if isinstance(val, str) else val

    @property
    def string(self):
        """Return the string inside the value. """
        if self.value:
            return self.value.string


class Coordination(Element):
    """ Coordinated clause with a conjunction. """

    def __init__(self, *coords, conj='and', features=None, parent=None,
                 **kwargs):
        super().__init__(COORDINATION, features, parent)
        self.coords = list()
        self.add_coordinate(*coords)
        self.set_feature('conj', conj)
        self.conj = conj
        self.pre_modifiers = list()
        self.complements = list()
        self.post_modifiers = list()
        # see if anything was passed from above...
        if 'pre_modifiers' in kwargs:
            self.pre_modifiers = str_to_elt(*kwargs['pre_modifiers'])
        if 'complements' in kwargs:
            self.complements = str_to_elt(*kwargs['complements'])
        if 'post_modifiers' in kwargs:
            self.post_modifiers = str_to_elt(*kwargs['post_modifiers'])

    def __bool__(self):
        """ Return True """
        return True

    def __eq__(self, other):
        if (not isinstance(other, Coordination)):
            return False
        else:
            return (self.coords == other.coords and
                    self.conj == other.conj and
                    super().__eq__(other))

    def __hash__(self):
        assert False, 'Coordination Element is not hashable'

    def __deepcopy__(self, memodict={}):
        copyobj = self.__class__(conj=self.conj, features=self.features,
                                 parent=self.parent)
        copyobj.coords = deepcopy(self.coords)
        copyobj.id = self.id
        return copyobj

    def add_front_modifier(self, *mods, pos=0):
        """ Add front modifiers to the first element. """
        # promote the element to a phrase
        if not is_phrase_t(self.coords[0]):
            self.coords[0] = NounPhrase(self.coords[0])
        self.coords[0].add_front_modifier(*mods, pos=pos)

    def add_pre_modifier(self, *mods, pos=0):
        """ Add pre-modifiers to the first element. """
        # promote the element to a phrase
        if not is_phrase_t(self.coords[0]):
            self.coords[0] = NounPhrase(self.coords[0])
        self.coords[0].add_pre_modifier(*mods, pos=pos)

    def add_complement(self, *mods, pos=None):
        """ Add complements to the last element. """
        # promote the element to a phrase
        if not is_phrase_t(self.coords[0]):
            self.coords[-1] = NounPhrase(self.coords[-1])
        self.coords[-1].add_complement(*mods, pos=pos)

    def add_post_modifier(self, *mods, pos=None):
        """ Add post modifiers to the last element. """
        # promote the element to a phrase
        if not is_phrase_t(self.coords[0]):
            self.coords[-1] = NounPhrase(self.coords[-1])
        self.coords[-1].add_post_modifier(*mods, pos=pos)

    def add_coordinate(self, *elts):
        """ Add one or more elements as a co-ordinate in the clause. """
        for e in str_to_elt(*elts):
            self.coords.append(e)

    def constituents(self):
        """ Return a generator to iterate through constituents. """
        yield self
        for c in self.coords:
            if hasattr(c, 'constituents'):
                yield from c.constituents()
            else:
                yield c

    def replace(self, one, another):
        """ Replace first occurance of one with another.
        Return True if successful.

        """
        logger.debug('Replacing "{}" in "{}" by "{}.'
                     .format(one, self, another))
        for i, o in enumerate(self.coords):
            if o == one:
                if another:
                    self.coords[i] = another
                else:
                    del self.coords[i]
                return True
            else:
                if o.replace(one, another):
                    return True
        return False

    @property
    def string(self):
        """Return the string inside the value. """
        return self.coords[0].string


class Phrase(Element):
    """ A base class for all kinds of phrases - elements containing other
        elements in specific places of the construct (front-, pre-, post-
        modifiers as well as the head of the phrase and any complements.

        Not every phrase has need for all of the kinds of modiffications.

    """

    def __init__(self, type=PHRASE, features=None, parent=None, **kwargs):
        super().__init__(type, features, parent)
        self.front_modifiers = list()
        self.pre_modifiers = list()
        self.head = Element()
        self.complements = list()
        self.post_modifiers = list()
        # see if anything was passed from above...
        if 'front_modifiers' in kwargs:
            self.front_modifiers = str_to_elt(*kwargs['front_modifiers'])
        if 'pre_modifiers' in kwargs:
            self.pre_modifiers = str_to_elt(*kwargs['pre_modifiers'])
        if 'head' in kwargs:
            self.head = kwargs['head']
        if 'complements' in kwargs:
            self.complements = str_to_elt(*kwargs['complements'])
        if 'post_modifiers' in kwargs:
            self.post_modifiers = str_to_elt(*kwargs['post_modifiers'])

    def __bool__(self):
        """ Return True """
        return True

    def __eq__(self, other):
        if not isinstance(other, Phrase):
            return False
        return (self.type == other.type and
                self.front_modifiers == other.front_modifiers and
                self.pre_modifiers == other.pre_modifiers and
                self.head == other.head and
                self.complements == other.complements and
                self.post_modifiers == other.post_modifiers and
                super().__eq__(other))

    def __hash__(self):
        assert False, 'Coordination Element is not hashable'

    def __iadd__(self, other):
        if is_adj_mod_t(other) or is_adv_mod_t(other):
            self.pre_modifiers.append(other)
        if isinstance(other, PrepositionalPhrase):
            self.add_complement(other)
        return self

    def __deepcopy__(self, memodict={}):
        copyobj = self.__class__(self.type, features=self.features,
                                 parent=self.parent)
        copyobj.id = self.id
        copyobj.front_modifiers = deepcopy(self.front_modifiers)
        copyobj.pre_modifiers = deepcopy(self.pre_modifiers)
        copyobj.head = deepcopy(self.head)
        copyobj.complements = deepcopy(self.complements)
        copyobj.post_modifiers = deepcopy(self.post_modifiers)
        return copyobj

    def accept(self, visitor, element='Phrase'):
        return super().accept(visitor, element)

    def set_front_modifiers(self, *mods):
        """ Set front-modifiers to the passed parameters. """
        self.front_modifiers = str_to_elt(*mods)

    def add_front_modifier(self, *mods, pos=0):
        """ Add one or more front-modifiers. """
        self._add_to_list(self.front_modifiers, *str_to_elt(*mods), pos=pos)

    def del_front_modifier(self, *mods):
        """ Remove one or more front-modifiers if present. """
        self._del_from_list(self.front_modifiers, *mods)

    def set_pre_modifiers(self, *mods):
        """ Set pre-modifiers to the passed parameters. """
        self.pre_modifiers = list(str_to_elt(*mods))

    def add_pre_modifier(self, *mods, pos=0):
        """ Add one or more pre-modifiers. """
        self._add_to_list(self.pre_modifiers, *str_to_elt(*mods), pos=pos)

    def del_pre_modifier(self, *mods):
        """ Delete one or more pre-modifiers if present. """
        self._del_from_list(self.pre_modifiers, *mods)

    def set_complements(self, *mods):
        """ Set complemets to the given ones. """
        self.complements = list(str_to_elt(*mods))

    def add_complement(self, *mods, pos=None):
        """ Add one or more complements. """
        self._add_to_list(self.complements, *str_to_elt(*mods), pos=pos)

    def del_complement(self, *mods):
        """ Delete one or more complements if present. """
        self._del_from_list(self.complements, *mods)

    def set_post_modifiers(self, *mods):
        """ Set post-modifiers to the given parameters. """
        self.post_modifiers = list(str_to_elt(*mods))

    def add_post_modifier(self, *mods, pos=None):
        """ Add one or more post-modifiers. """
        self._add_to_list(self.post_modifiers, *str_to_elt(*mods), pos=pos)

    def del_post_modifier(self, *mods):
        """ Delete one or more post-modifiers if present. """
        self._del_from_list(self.post_modifiers, *mods)

    def set_head(self, elt):
        """ Set head of the phrase to the given element. """
        if elt is None: elt = Element()
        self.head = String(elt) if isinstance(elt, str) else elt
        self.head.parent = self
        self.features.update(self.head.features)

    def yield_front_modifiers(self):
        """ Iterate through front modifiers. """
        for o in self.front_modifiers:
            for x in o.constituents():
                yield from x.constituents()

    def yield_pre_modifiers(self):
        """ Iterate through pre-modifiers. """
        for o in self.pre_modifiers:
            for x in o.constituents():
                yield from x.constituents()

    def yield_head(self):
        """ Iterate through the elements composing the head. """
        if self.head is not None:
            for x in self.head.constituents():
                yield from x.constituents()

    def yield_complements(self):
        """ Iterate through complements. """
        for o in self.complements:
            for x in o.constituents():
                yield from x.constituents()

    def yield_post_modifiers(self):
        """ Iterate throught post-modifiers. """
        for o in self.post_modifiers:
            for x in o.constituents():
                yield from x.constituents()

    def constituents(self):
        """ Return a generator to iterate through constituents. """
        yield self
        yield from self.yield_front_modifiers()
        yield from self.yield_pre_modifiers()
        yield from self.yield_head()
        yield from self.yield_complements()
        yield from self.yield_post_modifiers()

    # TODO: consider spliting the code below similarly to 'constituents()'
    def replace(self, one, another):
        """ Replace first occurance of one with another.
        Return True if successful.

        """
        for i, o in enumerate(self.front_modifiers):
            if o == one:
                if another is None:
                    del self.front_modifiers[i]
                else:
                    self.front_modifiers[i] = another
                return True
            else:
                if o.replace(one, another):
                    return True

        for i, o in enumerate(self.pre_modifiers):
            if o == one:
                if another is None:
                    del self.pre_modifiers[i]
                else:
                    self.pre_modifiers[i] = another
                return True
            else:
                if o.replace(one, another):
                    return True

        if self.head == one:
            for k in self.head.features.keys():
                if k in self.features:
                    del self.features[k]
            if hasattr(another, 'type') and self.type == another.type:
                if hasattr(self, 'spec') and hasattr(another, 'spec'):
                    self.spec = another.spec
                self.add_front_modifier(*another.front_modifiers)
                self.add_pre_modifier(*another.pre_modifiers)
                self.head = another.head
                self.add_complement(*another.complements)
                self.add_post_modifier(*another.post_modifiers)
            else:
                self.head = another
            self.features.update(another.features)
            return True
        elif self.head is not None:
            if self.head.replace(one, another):
                return True

        for i, o in enumerate(self.complements):
            if o == one:
                if another is None:
                    del self.complements[i]
                else:
                    self.complements[i] = another
                return True
            else:
                if o.replace(one, another):
                    return True

        for i, o in enumerate(self.post_modifiers):
            if o == one:
                if another is None:
                    del self.post_modifiers[i]
                else:
                    self.post_modifiers[i] = another
                return True
            else:
                if o.replace(one, another):
                    return True
        return False


class NounPhrase(Phrase):
    """
     * <UL>
     * <li>FrontModifier (eg, "some of")</LI>
     * <li>Specifier     (eg, "the")</LI>
     * <LI>PreModifier   (eg, "green")</LI>
     * <LI>Noun (head)   (eg, "apples")</LI>
     * <LI>complement    (eg, "that you liked")</LI>
     * <LI>PostModifier  (eg, "in the shop")</LI>
     * </UL>
     """

    def __init__(self, head=None, spec=None, features=None, parent=None,
                 **kwargs):
        super().__init__(NOUN_PHRASE, features, parent, **kwargs)
        self.spec = None
        self.set_spec(spec)
        self.set_head(head)

    def __eq__(self, other):
        if not isinstance(other, NounPhrase):
            return False
        return (self.spec == other.spec and
                self.head == other.head and
                super().__eq__(other))

    def __deepcopy__(self, memodict={}):
        copyobj = self.__class__(deepcopy(self.head), deepcopy(self.spec),
                                 features=self.features, parent=self.parent)
        copyobj.id = self.id
        copyobj.hash = self.hash
        return copyobj

    def set_spec(self, spec):
        """ Set the specifier (e.g., determiner) of the NounPhrase. """
        if spec is None: spec = Element()
        # convert str to String if necessary
        self.spec = String(spec) if isinstance(spec,
                                               str) else spec  # use raise_to_element

    def constituents(self):
        """ Return a generator to iterate through constituents. """
        yield self
        if self.spec is not None:
            for c in self.spec.constituents(): yield from c.constituents()
        yield from self.yield_front_modifiers()
        yield from self.yield_pre_modifiers()
        yield from self.yield_head()
        yield from self.yield_complements()
        yield from self.yield_post_modifiers()

    def replace(self, one, another):
        """ Replace first occurance of one with another.
        Return True if successful.

        """
        if self.spec == one:
            self.spec = another
            return True
        elif self.spec is not None:
            if self.spec.replace(one, another): return True

        return super().replace(one, another)


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

    def __init__(self, head=None, *compl, features=None, **kwargs):
        super().__init__(VERB_PHRASE, features, **kwargs)
        self.set_head(head)
        self.add_complement(*compl)

    def __deepcopy__(self, memodict={}):
        copyobj = self.__class__(deepcopy(self.head),
                                 features=self.features, parent=self.parent)
        copyobj.id = self.id
        copyobj.hash = self.hash
        copyobj.complements = deepcopy(self.complements)
        return copyobj

    def get_object(self):
        for c in self.complements:
            if c.has_feature('discourseFunction', 'OBJECT'):
                return c
        return None

    def remove_object(self):
        compls = list()
        for c in self.complements:
            if c.has_feature('discourseFunction', 'OBJECT'):
                continue
            else:
                compls.append(c)
        self.complements = compls

    def set_object(self, obj):
        self.remove_object()
        if obj is not None:
            if isinstance(obj, str): obj = String(obj)
            obj.set_feature('discourseFunction', 'OBJECT')
            self.complements.insert(0, obj)


class PrepositionalPhrase(Phrase):
    def __init__(self, head=None, *compl, features=None, **kwargs):
        super().__init__(PREPOSITIONAL_PHRASE, features, **kwargs)
        self.set_head(head)
        self.add_complement(*compl)

    def __deepcopy__(self, memodict={}):
        copyobj = self.__class__(deepcopy(self.head),
                                 features=self.features, parent=self.parent)
        copyobj.id = self.id
        copyobj.hash = self.hash
        copyobj.complements = deepcopy(self.complements)
        return copyobj


class AdverbPhrase(Phrase):
    def __init__(self, head=None, *compl, features=None, **kwargs):
        super().__init__(ADVERB_PHRASE, features, **kwargs)
        self.set_head(head)
        self.add_complement(*compl)

    def __deepcopy__(self, memodict={}):
        copyobj = self.__class__(deepcopy(self.head),
                                 features=self.features, parent=self.parent)
        copyobj.id = self.id
        copyobj.hash = self.hash
        copyobj.complements = deepcopy(self.complements)
        return copyobj


class AdjectivePhrase(Phrase):
    def __init__(self, head=None, *compl, features=None, **kwargs):
        super().__init__(ADJECTIVE_PHRASE, features, **kwargs)
        self.set_head(head)
        self.add_complement(*compl)

    def __deepcopy__(self, memodict={}):
        copyobj = self.__class__(deepcopy(self.head),
                                 features=self.features, parent=self.parent)
        copyobj.id = self.id
        copyobj.hash = self.hash
        copyobj.complements = deepcopy(self.complements)
        return copyobj


class Clause(Element):
    """ Clause - sentence.
    From simplenlg:
     * <UL>
     * <li>PreModifier (eg, "Yesterday")
     * <LI>Subject (eg, "John")
     * <LI>VerbPhrase (eg, "gave Mary an apple before school")
     * <LI>PostModifier (eg, ", didn't he?")
     * </UL>

    """

    subj = None
    vp = None

    def __init__(self, subj=None, vp=Element(), features=None, parent=None,
                 **kwargs):
        super().__init__(CLAUSE, features, parent=parent)
        self.front_modifiers = list()
        self.pre_modifiers = list()
        self.set_subj(raise_to_np(subj))
        self.set_vp(raise_to_vp(vp))
        self.complements = list()
        self.post_modifiers = list()
        # see if anything was passed from above...
        if 'front_modifiers' in kwargs:
            self.front_modifiers = str_to_elt(*kwargs['front_modifiers'])
        if 'pre_modifiers' in kwargs:
            self.pre_modifiers = str_to_elt(*kwargs['pre_modifiers'])
        if 'complements' in kwargs:
            self.complements = str_to_elt(*kwargs['complements'])
        if 'post_modifiers' in kwargs:
            self.post_modifiers = str_to_elt(*kwargs['post_modifiers'])

    def __bool__(self):
        """ Return True """
        return True

    def __eq__(self, other):
        if not isinstance(other, Clause):
            return False
        return (self.pre_modifiers == other.pre_modifiers and
                self.subj == other.subj and
                self.vp == other.vp and
                self.complements == other.complements and
                self.post_modifiers == other.post_modifiers and
                super().__eq__(other))

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
            raise ValueError(
                'Cannot add these up: "{}" + "{}"'.format(self, other))

    def __deepcopy__(self, memodict={}):
        copyobj = self.__class__(deepcopy(self.subj),
                                 deepcopy(self.vp),
                                 features=self.features,
                                 parent=self.parent)
        copyobj.id = self.id
        copyobj.front_modifiers = deepcopy(self.front_modifiers)
        copyobj.pre_modifiers = deepcopy(self.pre_modifiers)
        copyobj.complements = deepcopy(self.complements)
        copyobj.post_modifiers = deepcopy(self.post_modifiers)
        return copyobj

    def set_subj(self, subj):
        """ Set the subject of the clause. """
        # convert str to String if necessary
        self.subj = String(subj) if isinstance(subj, str) else (
            subj or Element())
        self.subj.parent = self

    def set_vp(self, vp):
        """ Set the vp of the clause. """
        self.vp = String(vp) if isinstance(vp, str) else vp
        self.vp.parent = self

    # TODO: test
    def set_object(self, obj):
        object = String(obj) if isinstance(obj, str) else obj
        object.set_feature('discourseFunction', 'OBJECT')
        object.parent = self
        self.add_complement(object)

    def setfeatures(self, features):
        """ Set features on the VerbPhrase. """
        if self.vp:
            self.vp.setfeatures(features)
        else:
            self.features = features

    def constituents(self):
        """ Return a generator to iterate through constituents. """
        yield self
        yield from self.yield_pre_modifiers()
        yield from self.subj.constituents()
        yield from self.vp.constituents()
        yield from self.yield_complements()
        yield from self.yield_post_modifiers()

    def replace(self, one, another):
        """ Replace first occurance of one with another.
        Return True if successful.

        """
        if self.subj == one:
            self.subj = raise_to_np(another)
            self.subj.parent = self
            return True
        elif self.subj is not None:
            if self.subj.replace(one, another):
                return True

        if self.vp == one:
            self.vp = raise_to_vp(another)
            self.vp.parent = self
            return True
        elif self.vp is not None:
            if self.vp.replace(one, another):
                return True

        return super().replace(one, another)

    def set_front_modifiers(self, *mods):
        """ Set front-modifiers to the passed parameters. """
        self.front_modifiers = list(str_to_elt(*mods))

    def add_front_modifier(self, *mods, pos=0):
        """ Add one or more front-modifiers. """
        self._add_to_list(self.front_modifiers, *str_to_elt(*mods), pos=pos)

    def del_front_modifier(self, *mods):
        """ Remove one or more front-modifiers if present. """
        self._del_from_list(self.front_modifiers, *mods)

    def yield_front_modifiers(self):
        """ Iterate through pre-modifiers. """
        for o in self.front_modifiers:
            for x in o.constituents():
                yield from x.constituents()

    def set_pre_modifiers(self, *mods):
        """ Set pre-modifiers to the passed parameters. """
        self.pre_modifiers = list(str_to_elt(*mods))

    def add_pre_modifier(self, *mods, pos=0):
        """ Add one or more pre-modifiers. """
        self._add_to_list(self.pre_modifiers, *str_to_elt(*mods), pos=pos)

    def del_pre_modifier(self, *mods):
        """ Delete one or more pre-modifiers if present. """
        self._del_from_list(self.pre_modifiers, *mods)

    def yield_pre_modifiers(self):
        """ Iterate through pre-modifiers. """
        for o in self.pre_modifiers:
            for x in o.constituents():
                yield from x.constituents()

    def set_complements(self, *mods):
        """ Set complemets to the given ones. """
        self.complements = list(str_to_elt(*mods))

    def add_complement(self, *mods, pos=None):
        """ Add one or more complements. """
        self._add_to_list(self.complements, *str_to_elt(*mods), pos=pos)

    def del_complement(self, *mods):
        """ Delete one or more complements if present. """
        self._del_from_list(self.complements, *mods)

    def yield_complements(self):
        """ Iterate through complements. """
        for o in self.complements:
            for x in o.constituents():
                yield from x.constituents()

    def set_post_modifiers(self, *mods):
        """ Set post-modifiers to the given parameters. """
        self.post_modifiers = list(str_to_elt(*mods))

    def add_post_modifier(self, *mods, pos=None):
        """ Add one or more post-modifiers. """
        self._add_to_list(self.post_modifiers, *str_to_elt(*mods), pos=pos)

    def del_post_modifier(self, *mods):
        """ Delete one or more post-modifiers if present. """
        self._del_from_list(self.post_modifiers, *mods)

    def yield_post_modifiers(self):
        """ Iterate through pre-modifiers. """
        for o in self.post_modifiers:
            for x in o.constituents():
                yield from x.constituents()


def raise_to_np(phrase):
    """Take the current phrase and raise it to an NP.
    If `phrase` is a Noun it will be promoted to NP and used as a head;
    If `phrase` is a CC its coordinants will be raised to NPs

    """
    if isinstance(phrase, Coordination):
        phrase.coords = [raise_to_np(c) for c in phrase.coords]
        return phrase
    if isinstance(phrase, String):
        return NounPhrase(head=phrase)
    if isinstance(phrase, Word):
        return NounPhrase(head=phrase)
    # if isinstance(phrase, Var):
    #     return NounPhrase(head=phrase)
    return phrase


def raise_to_vp(phrase):
    """Take the current phrase and raise it to a VP.
    If `phrase` is a Word it will be promoted to VP and used as a head;
    If `phrase` is a CC its coordinants will be raised to VPs

    """
    if isinstance(phrase, Coordination):
        phrase.coords = [raise_to_vp(c) for c in phrase.coords]
        return phrase
    if isinstance(phrase, String):
        return VerbPhrase(head=phrase)
    if isinstance(phrase, Word):
        return VerbPhrase(head=phrase)
    # if isinstance(phrase, Var):
    #     return VerbPhrase(head=phrase)
    return phrase


def raise_to_element(element):
    """Raise the given thing to an element (e.g., String). """
    if not isinstance(element, Element):
        return String(str(element))  # use str() in case of numbers
    return element


class ElementEncoder(json.JSONEncoder):
    def default(self, python_object):
        if isinstance(python_object, Element):
            return {'__class__': str(type(python_object)),
                    '__value__': python_object.__dict__}
        return super(ElementEncoder, self).default(python_object)


class ElementDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        kwargs['object_hook'] = ElementDecoder.from_json
        super(ElementDecoder, self).__init__(*args, **kwargs)

    @staticmethod
    def from_json(json_object):
        if '__class__' in json_object:
            if json_object['__class__'] == "<class 'nlglib.structures.microplanning.Element'>":
                return Element.from_dict(json_object['__value__'])
            if json_object['__class__'] == "<class 'nlglib.structures.microplanning.String'>":
                return String.from_dict(json_object['__value__'])
            if json_object['__class__'] == "<class 'nlglib.structures.microplanning.Word'>":
                return Word.from_dict(json_object['__value__'])
            if json_object['__class__'] == "<class 'nlglib.structures.microplanning.Var'>":
                return Var.from_dict(json_object['__value__'])
            if json_object['__class__'] == "<class 'nlglib.structures.microplanning.Phrase'>":
                return Phrase.from_dict(json_object['__value__'])
            if json_object['__class__'] == "<class 'nlglib.structures.microplanning.Clause'>":
                return Clause.from_dict(json_object['__value__'])
            if json_object['__class__'] == "<class 'nlglib.structures.microplanning.NounPhrase'>":
                return NounPhrase.from_dict(json_object['__value__'])
            if json_object['__class__'] == "<class 'nlglib.structures.microplanning.VerbPhrase'>":
                return VerbPhrase.from_dict(json_object['__value__'])
            if json_object[
                '__class__'] == "<class 'nlglib.structures.microplanning.PrepositionalPhrase'>":
                return PrepositionalPhrase.from_dict(json_object['__value__'])
            if json_object[
                '__class__'] == "<class 'nlglib.structures.microplanning.AdjectivePhrase'>":
                return AdjectivePhrase.from_dict(json_object['__value__'])
            if json_object['__class__'] == "<class 'nlglib.structures.microplanning.AdverbPhrase'>":
                return AdverbPhrase.from_dict(json_object['__value__'])
            if json_object['__class__'] == "<class 'nlglib.structures.microplanning.Coordination'>":
                return Coordination.from_dict(json_object['__value__'])
        return json_object
