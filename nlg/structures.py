
import logging
from urllib.parse import quote_plus
import json
import inspect


def get_log():
    return logging.getLogger(__name__)


get_log().addHandler(logging.NullHandler())


# indentation constant for printing XML
indent = '  '


""" Data structures used by other packages. """

# macroplanning level structures
#   for content determination and content structuring


def enum(*sequential, **named):
    """ This functions declares a new type 'enum' that acts as an enum. """
    enums = dict(zip(sequential, range(len(sequential))), **named)
    reverse = dict((value, key) for key, value in enums.items())
    enums['reverse_mapping'] = reverse
    return type('Enum', (), enums)


""" Rhetorical Structure Theory relations """
RST = enum('Elaboration', 'Exemplification',
           'Contrast', 'Exception', 'Set',
           'List', 'Sequence', 'Alternative',
           'Conjunction', 'Disjunction',
           'Leaf'
           )


class Document:
    """ The class Document represents a container holding information about
        a document - title and a list of sections.

    """
    def __init__(self, title, *sections):
        """ Create a new Document instance with given title and with
            zero or more sections.

        """
        self.title = title
        self.sections = [s for s in sections if s is not None]

    def __repr__(self):
        descr = (repr(self.title) + '\n' +
                 '\n\n'.join([repr(s) for s in self.sections if s is not None]))
        return 'Document:\ntitle: %s' % descr.strip()

    def __str__(self):
        descr = (str(self.title) + '\n' +
                '\n\n'.join([str(s) for s in self.sections if s is not None]))
        return descr

    def __eq__(self, other):
        return (isinstance(other, Document) and
                self.title == other.title and
                self.sections == other.sections)

    def constituents(self):
        """ Return a generator to iterate through the elements. """
        yield self.title
        for x in self.sections: yield from x.constituents()


class Section:
    """ The class Section represents a container holding information about
        a section of a document - a title and a list of paragraphs.

    """
    def __init__(self, title, *paragraphs):
        """ Create a new section with given title and zero or more paragraphs.

        """
        self.title = title
        self.paragraphs = [p for p in paragraphs if p is not None]

    def __repr__(self):
        descr = (repr(self.title) + '\n' +
                '\n'.join([repr(p) for p in self.paragraphs if p is not None]))
        return 'Section:\ntitle: %s' % descr.strip()

    def __str__(self):
        descr = (str(self.title) + '\n' +
                '\n'.join([str(p) for p in self.paragraphs if p is not None]))
        return descr

    def __eq__(self, other):
        return (isinstance(other, Section) and
                self.title == other.title and
                self.paragraphs == other.paragraphs)

    def constituents(self):
        """ Return a generator to iterate through the elements. """
        yield self.title
        for x in self.paragraphs: yield from x.constituents()


class Paragraph:
    """ The class Paragraph represents a container holding information about
        a paragraph of a document - a list of messages.

    """
    def __init__(self, *messages):
        """ Create a new Paragraph with zero or more messages. """
        self.messages = [m for m in messages if m is not None]

    def __repr__(self):
        descr = '; '.join([repr(m) for m in self.messages if m is not None])
        return 'Paragraph (%d):\n%s' % (len(self.messages), descr.strip())

    def __str__(self):
        descr = ('\t' +
                 '; '.join([str(m) for m in self.messages if m is not None]))
        return descr

    def __eq__(self, other):
        return (isinstance(other, Paragraph) and
                self.messages == other.messages)

    def constituents(self):
        """ Return a generator to iterate through the elements. """
        for x in self.messages: yield from x.constituents()


class Message:
    """ A representation of a message (usually a sentence).
        A message has a nucleus and zero or more satelites joined
        by an RST (Rhetorical Structure Theory) relation.

    """
    def __init__(self, rel, nucleus, *satelites, features=None):
        """ Create a new Message with given relation between the nucleus
            and zero or more satelites.

        """
        self.rst = rel
        self.nucleus = nucleus
        self.satelites = [s for s in satelites if s is not None]
        self.marker = ''
        self._features = features or {}

    def __repr__(self):
        descr = ' '.join([repr(x) for x in
                  ([self.nucleus] + self.satelites) if x is not None ])
        if descr == '': descr = '_empty_'
        return 'Message (%s): %s' % (self.rst, descr.strip())

    def __str__(self):
        descr = ' '.join( [str(x) for x in
            ([self.nucleus] + self.satelites) if x is not None ] )
        return (descr.strip() if descr is not None else '')

    def __eq__(self, other):
        return (isinstance(other, Message) and
                self.rst == other.rst and
                self.nucleus == other.nucleus and
                self.satelites == other.satelites)

    def constituents(self):
        """ Return a generator to iterate through the elements. """
        if self.nucleus:
            if hasattr(self.nucleus, 'constituents'):
                yield from self.nucleus.constituents()
            else:
                yield self.nucleus
        for x in self.satelites:
            if hasattr(x, 'constituents'):
                yield from x.constituents()
            else:
                yield x


class RhetRep:
    """ A representation of a rhetorical structure.
    The data structure is from RAGS (Mellish et. al. 2006) and it represents
    an element in the rhetorical structure of the document. Each element has
    a nucleus, a satelite and a relation name. Some relations allow multiple
    nuclei instead of a satelite (e.g., lists).

    Rhetorical structure is a tree. The children can be either RhetReps
    or MsgSpecs.

    """
    def __init__(self, relation, *nuclei, satelite=None, marker=None):
        self.relation = relation
        self.nucleus = list(nuclei)
        self.satelite = satelite
        self.is_multinuclear = (len(nuclei) > 1)
        self.marker = marker

    def to_xml(self, lvl=0):
        spaces = indent * lvl
        data = spaces + '<rhetrep name="' + str(self.relation) + '">\n'
        data += indent + spaces + '<marker>' + self.marker + '</marker>\n'
        if self.is_multinuclear:
            data += ''.join([e.to_xml(lvl + 1)
                for e in self.nucleus])
        else:
            data += ''.join([e.to_xml(lvl + 1)
                for e in (self.nucleus, self.satelite)])
        data += spaces + '</rhetrep>\n'
        return data

    def to_str(self):
        pass


class SemRep:

    def __init__(self, clause, **features):
        self.clause = clause
        self.features = features or dict()

    def to_xml(self, lvl):
        spaces = indent * lvl
        data = spaces + '<semrep>\n'
        data += spaces + indent + str(self.clause) + '\n'
        data += spaces + '</semrep>\n'
        return data


class MsgSpec:
    """ MsgSpec specifies an interface for various message specifications.
    Because the specifications are domain dependent, this is just a convenience
    interface that allows the rest of the library to operate on the messages.

    The name of the message is used during lexicalisation where the name is
    looked up in an ontology to find corresponding syntactic frame. To populate
    the frame, the lexicaliser finds all variables and uses their names
    as a key to look up the values in the corresponding message. For example,
    if the syntactic structure in the domain ontology specifies a variable
    named 'foo', the lexicaliser will call msg.value_for('foo'), which
    in turn calls self.foo(). This should return the value for the key 'foo'.

    """
    def __init__(self, name, features=None):
        self.name = name
        self._features = features or {}

    def __repr__(self):
        return 'MsgSpec({0}, {1})'.format(self.name, self._features)

    def __str__(self):
        return str(self.name)

    def __eq__(self, other):
        return (isinstance(other, type(self)) and
                self.name == other.name)

    def value_for(self, data_member):
        """ Return a value for an argument using introspection. """
        if not hasattr(self, data_member):
            raise ValueError('Error: cannot find value for key: %s' %
                                data_member)
        m = getattr(self, data_member)
        if not hasattr(m, '__call__'):
            raise ValueError('Error: cannot call the method "%s"' %
                                data_member)
        return m()

    @classmethod
    def instantiate(Klass, data):
        return None


class DiscourseContext:
    """ A class that captures the discourse referents and history. """

    def __init__(self):
        self.referents = []
        self.history = []
        self.referent_info = {}


class OperatorContext:
    """ A class that captures the operators in a logical formula. """

    def __init__(self):
        self.variables = []
        self.symbols = []
        self.negations = 0



################################################################################
#                                                                              #
#                              microplanning                                   #
#                                                                              #
################################################################################


class ElemntCoder(json.JSONEncoder):
    @staticmethod
    def to_json(python_object):
        if isinstance(python_object, Element):
            return {'__class__': str(type(python_object)),
                    '__value__': python_object.__dict__}
        raise TypeError(repr(python_object) + ' is not JSON serializable')

    @staticmethod
    def from_json(json_object):
        if '__class__' in json_object:
            if json_object['__class__'] == "<class 'nlg.structures.Element'>":
                return Element.from_dict(json_object['__value__'])
            if json_object['__class__'] == "<class 'nlg.structures.String'>":
                return String.from_dict(json_object['__value__'])
            if json_object['__class__'] == "<class 'nlg.structures.Word'>":
                return Word.from_dict(json_object['__value__'])
            if json_object['__class__'] == "<class 'nlg.structures.PlaceHolder'>":
                return PlaceHolder.from_dict(json_object['__value__'])
            if json_object['__class__'] == "<class 'nlg.structures.Phrase'>":
                return Phrase.from_dict(json_object['__value__'])
            if json_object['__class__'] == "<class 'nlg.structures.Clause'>":
                return Clause.from_dict(json_object['__value__'])
            if json_object['__class__'] == "<class 'nlg.structures.NounPhrase'>":
                return NounPhrase.from_dict(json_object['__value__'])
            if json_object['__class__'] == "<class 'nlg.structures.VerbPhrase'>":
                return VerbPhrase.from_dict(json_object['__value__'])
            if json_object['__class__'] == "<class 'nlg.structures.PrepositionalPhrase'>":
                return PrepositionalPhrase.from_dict(json_object['__value__'])
            if json_object['__class__'] == "<class 'nlg.structures.AdjectivePhrase'>":
                return AdjectivePhrase.from_dict(json_object['__value__'])
            if json_object['__class__'] == "<class 'nlg.structures.AdverbPhrase'>":
                return AdverbPhrase.from_dict(json_object['__value__'])
            if json_object['__class__'] == "<class 'nlg.structures.Coordination'>":
                return Coordination.from_dict(json_object['__value__'])

        return json_object


# types of clauses:
ELEMENT     = 0 # abstract
STRING      = 1
WORD        = 2
PLACEHOLDER = 3
CLAUSE      = 4

COORDINATION  = 5
SUBORDINATION = 6

PHRASE      = 10 # abstract
NOUNPHRASE  = 11
VERBPHRASE  = 12
PREPPHRASE  = 13
ADJPHRASE   = 14
ADVPHRASE   = 15


# visitor names
VisitorNames = {
    ELEMENT     : 'visit_element',
    STRING      : 'visit_string',
    WORD        : 'visit_word',
    PLACEHOLDER : 'visit_placeholder',
    CLAUSE      : 'visit_clause',

    COORDINATION  : 'visit_coordination',
    SUBORDINATION : 'visit_subordination',

    PHRASE     : 'visit_phrase',
    NOUNPHRASE : 'visit_np',
    VERBPHRASE : 'visit_vp',
    PREPPHRASE : 'visit_pp',
    ADJPHRASE  : 'visit_adjp',
    ADVPHRASE  : 'visit_advp',
}


def is_element_t(o):
    """ An object is an element if it has attr _type and one of the types. """
    if not hasattr(o, '_type'): return False
    else: return o._type in VisitorNames


def is_phrase_t(o):
    """ An object is a phrase type if it is a phrase or a coordination of 
    phrases.
    
    """
    return (is_element_t(o) and
            (o._type in {PHRASE, NounPhrase, VerbPhrase, PrepositionalPhrase, ADJPHRASE, ADVPHRASE} or
             (o._type == COORDINATION and
             (o.coord == [] or is_phrase_t(o.coord[0])))))


def is_clause_t(o):
    """ An object is a clause type if it is a clause, subordination or 
    a coordination of clauses. 
    
    """
    return (is_element_t(o) and
            (o._type in {CLAUSE, SUBORDINATION} or
             (o._type == COORDINATION and
              (o.coord == [] or is_clause_t(o.coord[0])))))


def str_to_elt(*params):
    """ Check that all params are Elements and convert
    and any strings to String.

    """
    fn = lambda x: String(x) if isinstance(x, str) else x
    return list(map(fn, params))


class Element:
    """ A base class representing an NLG element.
        Aside for providing a base class for othe kinds of NLG elements,
        the class also implements basic functionality for elements.

    """
    def __init__(self, type=ELEMENT, features=None):
        self.id = 0 # this is useful for replacing elements
        self._type = ELEMENT
        self._visitor_name = VisitorNames[type]
        self._features = features or dict()

    def __bool__(self):
        """ Because Element is abstract, it will evaluate to false. """
        return False

    def __eq__(self, other):
        if not is_element_t(other): return False
        if not self._type is other._type: return False
        return (self.id == other.id and
                self._features == other._features)

    @classmethod
    def from_dict(Cls, dct):
        o = Cls()
        o.__dict__ = dct
        return o

    def to_JSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, indent=4)

    def __repr__(self):
        from nlg.microplanning import ReprVisitor
        v = ReprVisitor()
        self.accept(v)
        return str(v)

    def __str__(self):
        from nlg.microplanning import StrVisitor
        v = StrVisitor()
        self.accept(v)
        return str(v)

    def accept(self, visitor, element='Element'):
        """Implementation of the Visitor pattern."""
        if self._visitor_name == None:
            raise ValueError('Error: visit method of uninitialized visitor '
                             'called!')
        # get the appropriate method of the visitor instance
        m = getattr(visitor, self._visitor_name)
        # ensure that the method is callable
        if not hasattr(m, '__call__'):
            raise ValueError('Error: cannot call undefined method: %s on '
                             'visitor' % self._visitor_name)
        sig = inspect.signature(m)
        # and finally call the callback
        if len(sig.parameters) == 1:
            return m(self)
        if len(sig.parameters) == 2:
            return m(self, element)


    def features_to_xml_attributes(self):
        features = ""
        for (k, v) in self._features.items():
            features += '%s="%s" ' % (quote_plus(str(k)), quote_plus(str(v)))
        features = features.strip()
        if features != '':
            return ' ' + features
        return ''

    def set_feature(self, feature, value):
        """ Add a feature to the feature set.
        If the feature exists, overwrite the old value.

        """
        self._features[feature] = value

    def has_feature(self, feature, value=None):
        """ Return True if the element has the given feature. 
        If a value is given, return true if the feature matches the value,
        otherwise return true if the element has some value for the feature.
        
        """
        if feature in self._features:
            if value is None: return True
            return value == self._features[feature]
        return False

    def get_feature(self, feature):
        """ Return value for given feature or None. """
        return self._features[feature]

    def feature(self, feat):
        """ Return value for given feature or None. """
        if feat in self._features: return self._features[feat]
        else: return None

    def del_feature(self, feat, val=None):
        """ Delete a feature, if the element has it else do nothing.
        If val is None, delete whathever value is assigned to the feature.
        Otherwise only delete the feature if it has matching value.

        """
        if feat in self._features:
            if val is not None: del self._features[feat]
            elif val == self._features[feat]: del self._features[feat]

    def add_features(self, features):
        """ Add the given features (dict) to the existing features. """
        for k, v in features.items():
            self._features[k] = v

    def constituents(self):
        """ Return a generator representing constituents of an element. """
        return []

    def arguments(self):
        """ Return any arguments (placeholders) from the elemen as a generator.

        """
        return list(filter(lambda x: isinstance(x, PlaceHolder),
                           self.constituents()))

    def replace(self, one, another):
        """ Replace first occurance of one with another.
        Return True if successful.

        """
        return False # basic implementation does nothing

    def replace_argument(self, arg_id, repl):
        """ Replace an argument with given id by repl if such argumen exists."""
        for a in self.arguments():
            if a.id == arg_id:
                return self.replace(a, repl)
        return False

    def replace_arguments(self, *args, **kwargs):
        """ Replace arguments with ids in the kwargs by the corresponding
        values.
        Replacements can be passed as a single dictionary or a kwarg list
        (e.g., arg1=x, arg2=y, ...)

        """
        # FIXME: this does not look correct...
        if len(args) > 0 and len(args) > 1:
            raise ValueError('too many parameters')
        elif len(args) > 0:
            for k, v in args[0]:
                self.replace_argument(k, v)
        else:
            for k, v in kwargs.items():
                self.replace_argument(k, v)

    @staticmethod
    def _add_to_list(lst, *mods):
        """ Add modifiers to the given list. Convert any strings to String. """
        for p in str_to_elt(*mods):
            if p not in lst: lst.append(p)

    @staticmethod
    def _del_from_list(lst, *mods):
        """ Delete elements from a list. Convert any strings to String. """
        for p in str_to_elt(*mods):
            if p in lst: lst.remove(p)


class String(Element):
    """ String is a basic element representing canned text. """
    def __init__(self, val='', features=None):
        super().__init__(STRING, features)
        self.val = val

    def __bool__(self):
        """ Return True if the string is non-empty. """
        return len(self.val) > 0
    
    def __eq__(self, other):
        if (not isinstance(other, String)):
            return False
        return (self.val == other.val and
                super().__eq__(other))

    def constituents(self):
        return [self]


class Word(Element):
    """ Word represents word and its corresponding POS (Part-of-Speech) tag. """
    def __init__(self, word, pos='ANY', features=None, base=None):
        super().__init__(WORD, features)
        self.word = word
        self.pos = pos
        self.base = base or word
        self.do_inflection = False
    
    def __bool__(self):
        """ Return True """
        return True

    def __eq__(self, other):
        if (not isinstance(other, Word)):
            return False
        return (self.word == other.word and
                self.pos == other.pos and
                super().__eq__(other))

    def constituents(self):
        return [self]


class PlaceHolder(Element):
    """ An element used as a place-holder in a sentence. The purpose of this
        element is to make replacing arguments easier. For example, in a plan
        one might want to replace arguments of an action with the instantiated
        objects
        E.g.,   move (x, a, b) -->
                move PlaceHolder(x) from PlaceHolder(a) to PlaceHolder(b) -->
                move (the block) from (the table) to (the green block)

    """
    def __init__(self, id=None, obj=None, features=None):
        super().__init__(PLACEHOLDER, features)
        self.id = id
        self.set_value(obj)
    
    def __bool__(self):
        """ Return True """
        return True

    def __eq__(self, other):
        if (not isinstance(other, PlaceHolder)):
            return False
        else:
            return (self.id == other.id and
                    self.value == other.value and
                    super().__eq__(other))

    def constituents(self):
        return [self]

    def set_value(self, val):
        if val is None: val = self.id
        self.value = String(val) if isinstance(val, str) else val


class Coordination(Element):
    """ Coordinated clause with a conjunction. """

    def __init__(self, *coords, conj='and', features=None):
        super().__init__(COORDINATION, features)
        self.coords = list()
        self.add_coordinate(*coords)
        self.set_feature('conj', conj)
        self.conj = conj

    def __bool__(self):
        """ Return True """
        return True

    def __eq__(self, other):
        if (not isinstance(other, Coordination)):
            return False
        else:
            return (self.coords == other.coords and
                    super().__eq__(other))

    def add_coordinate(self, *elts):
        """ Add one or more elements as a co-ordinate in the clause. """
        for e in str_to_elt(*elts):
            self.coords.append(e)

    def constituents(self):
        """ Return a generator to iterate through constituents. """
        if self.coords is not None:
            for c in self.coords:
                if hasattr(c, 'constituents'):
                    yield from c.constituents()
                else:
                    yield c

    def replace(self, one, another):
        """ Replace first occurance of one with another.
        Return True if successful.

        """
        for i, o in enumerate(self.coords):
            if o == one:
                if another: self.coords[i] = another
                else: del self.coords[i]
                return True
        return False


# Coordination is a synonym for coordination
class Coordination(Coordination): pass


# FIXME: incomplete implementation -- who is parent and who is subord child?
class Subordination(Element):
    """ Subordinate elment. """

    def __init__(self, main, subordinate, features=None):
        super().__init__(SUBORDINATION, features)
        self.main = main
        self.subordinate = subordinate

    def __bool__(self):
        """ Return True """
        return True

    def __eq__(self, other):
        if not isinstance(other, Subordination):
            return False
        else:
            return (self.main == other.main and
                    self.subordinate == other.subordinate and
                    super().__eq__(other))


class Phrase(Element):
    """ A base class for all kinds of phrases - elements containing other
        elements in specific places of the construct (front-, pre-, post-
        modifiers as well as the head of the phrase and any complements.

        Not every phrase has need for all of the kinds of modiffications.

    """
    def __init__(self, type=PHRASE, features=None, **kwargs):
        super().__init__(type, features)
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
        if (not isinstance(other, Phrase)):
            return False
        return (self._type == other._type and
                self.front_modifiers == other.front_modifiers and
                self.pre_modifiers == other.pre_modifiers and
                self.head == other.head and
                self.complements == other.complements and
                self.post_modifiers == other.post_modifiers and
                super().__eq__(other))

    def accept(self, visitor, element='Phrase'):
        return super().accept(visitor, element)

    def set_front_modifiers(self, *mods):
        """ Set front-modifiers to the passed parameters. """
        self.front_modifiers = list(str_to_elt(*mods))

    def add_front_modifier(self, *mods):
        """ Add one or more front-modifiers. """
        self._add_to_list(self.front_modifiers, *mods)

    def del_front_modifier(self, *mods):
        """ Remove one or more front-modifiers if present. """
        self._del_from_list(self.front_modifiers, *mods)

    def set_pre_modifiers(self, *mods):
        """ Set pre-modifiers to the passed parameters. """
        self.pre_modifiers = list(str_to_elt(*mods))

    def add_pre_modifier(self, *mods):
        """ Add one or more pre-modifiers. """
        self._add_to_list(self.pre_modifiers, *mods)

    def del_pre_modifier(self, *mods):
        """ Delete one or more pre-modifiers if present. """
        self._del_from_list(self.pre_modifiers, *mods)

    def set_complements(self, *mods):
        """ Set complemets to the given ones. """
        self.complements = list(str_to_elt(*mods))

    def add_complement(self, *mods):
        """ Add one or more complements. """
        self._add_to_list(self.complements, *mods)

    def del_complement(self, *mods):
        """ Delete one or more complements if present. """
        self._del_from_list(self.complements, *mods)

    def set_post_modifiers(self, *mods):
        """ Set post-modifiers to the given parameters. """
        self.post_modifiers = list(str_to_elt(*mods))

    def add_post_modifier(self, *mods):
        """ Add one or more post-modifiers. """
        self._add_to_list(self.post_modifiers, *mods)

    def del_post_modifier(self, *mods):
        """ Delete one or more post-modifiers if present. """
        self._del_from_list(self.post_modifiers, *mods)

    def set_head(self, elt):
        """ Set head of the phrase to the given element. """
        if elt is None: elt = Element()
        self.head = String(elt) if isinstance(elt, str) else elt

    def yield_front_modifiers(self):
        """ Iterate through front modifiers. """
        for o in self.front_modifiers:
            for x in o.constituents():
                yield x

    def yield_pre_modifiers(self):
        """ Iterate through pre-modifiers. """
        for o in self.pre_modifiers:
            for x in o.constituents():
                yield x

    def yield_head(self):
        """ Iterate through the elements composing the head. """
        if self.head is not None:
            for x in self.head.constituents():
                yield x

    def yield_complements(self):
        """ Iterate through complements. """
        for o in self.complements:
            for x in o.constituents():
                yield x

    def yield_post_modifiers(self):
        """ Iterate throught post-modifiers. """
        for o in self.post_modifiers:
            for x in o.constituents():
                yield x

    def constituents(self):
        """ Return a generator to iterate through constituents. """
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
            self.head = another
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
                    del self.front_modifiers[i]
                else:
                    self.front_modifiers[i] = another
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
     * <LI>PostModifier  (eg, "in the shop")</LI>
     * </UL>
     """
    def __init__(self, head=None, spec=None, features=None, **kwargs):
        super().__init__(NOUNPHRASE, features, **kwargs)
        self.set_spec(spec)
        self.set_head(head)

    def __eq__(self, other):
        if (not isinstance(other, NounPhrase)):
            return False
        return (self.spec == other.spec and
                self.head == other.head and
                super().__eq__(other))

    def set_spec(self, spec):
        """ Set the specifier (e.g., determiner) of the NounPhrase. """
        if spec is None: spec = Element()
        # convert str to String if necessary
        self.spec = String(spec) if isinstance(spec, str) else spec

    def constituents(self):
        """ Return a generator to iterate through constituents. """
        if self.spec is not None:
            for c in self.spec.constituents(): yield c
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
        super().__init__(VERBPHRASE, features, **kwargs)
        self.set_head(head)
        self.add_complement(*compl)

    def get_object(self):
        for c in self.complements:
            if ('discourseFunction' in c.features and
                c.features['discourseFunction'] == 'OBJECT'):
                return c
        return None

    def remove_object(self):
        compls = list()
        for c in self.complements:
            if ('discourseFunction' in c.features and
                c.features['discourseFunction'] == 'OBJECT'):
                continue
            else:
                compls.append(c)
        self.complements = compls

    def set_object(self, obj):
        self.remove_object()
        if obj is not None:
            if isinstance(obj, str): obj = String(obj)
            obj.features['discourseFunction'] = 'OBJECT'
            self.complements.insert(0, obj)

    def to_xml(self, element):
        features = self.features_to_xml_attributes()
        text = '<%s xsi:type="VPPhraseSpec" %s>\n' % (element, features)
        return text


class PrepositionalPhrase(Phrase):
    def __init__(self, head=None, *compl, features=None, **kwargs):
        super().__init__(PREPPHRASE, features, **kwargs)
        self.set_head(head)
        self.add_complement(*compl)


class AdverbPhrase(Phrase):
    def __init__(self, head=None, *compl, features=None, **kwargs):
        super().__init__(ADVPHRASE, features, **kwargs)
        self.set_head(head)
        self.add_complement(*compl)


class AdjectivePhrase(Phrase):
    def __init__(self, head=None, *compl, features=None, **kwargs):
        super().__init__(ADJPHRASE, features, **kwargs)
        self.set_head(head)
        self.add_complement(*compl)


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

    def __init__(self, subj=Element(), vp=Element(), features=None, **kwargs):
        super().__init__(CLAUSE, features)
        self.pre_modifiers = list()
        self.post_modifiers = list()
        self.set_subj(subj)
        self.set_vp(vp)
        # see if anything was passed from above...
        if 'pre_modifiers' in kwargs:
            self.pre_modifiers = str_to_elt(*kwargs['pre_modifiers'])
        if 'post_modifiers' in kwargs:
            self.post_modifiers = str_to_elt(*kwargs['post_modifiers'])

    def __bool__(self):
        """ Return True """
        return True

    def __eq__(self, other):
        if (not isinstance(other, Clause)):
            return False
        return (self.pre_modifiers == other.pre_modifiers and
                self.subj == other.subj and
                self.vp == other.vp and
                self.post_modifiers == other.post_modifiers and
                super().__eq__(other))

    def set_subj(self, subj):
        """ Set the subject of the clause. """
        # convert str to String if necessary
        self.subj = String(subj) if isinstance(subj, str) else subj

    def set_vp(self, vp):
        """ Set the vp of the clause. """
        self.vp = String(vp) if isinstance(vp, str) else vp

    def set_features(self, features):
        """ Set features on the VerbPhrase. """
        if self.vp:
            self.vp.set_features(features)

    def constituents(self):
        """ Return a generator to iterate through constituents. """
        yield from self.yield_pre_modifiers()
        yield from self.subj.constituents()
        yield from self.vp.constituents()
        yield from self.yield_post_modifiers()

    def replace(self, one, another):
        """ Replace first occurance of one with another.
        Return True if successful.

        """
        if self.subj == one:
            self.subj = another
            return True
        elif self.subj is not None:
            if self.subj.replace(one, another): return True

        if self.vp == one:
            self.vp = another
            return True
        elif self.vp is not None:
            if self.vp.replace(one, another): return True

        return super().replace(one, another)

    def set_pre_modifiers(self, *mods):
        """ Set pre-modifiers to the passed parameters. """
        self.pre_modifiers = list(str_to_elt(*mods))

    def add_pre_modifier(self, *mods):
        """ Add one or more pre-modifiers. """
        self._add_to_list(self.pre_modifiers, *mods)

    def del_pre_modifier(self, *mods):
        """ Delete one or more pre-modifiers if present. """
        self._del_from_list(self.pre_modifiers, *mods)

    def yield_pre_modifiers(self):
        """ Iterate through pre-modifiers. """
        for o in self.pre_modifiers:
            for x in o.constituents():
                yield x

    def set_post_modifiers(self, *mods):
        """ Set post-modifiers to the given parameters. """
        self.post_modifiers = list(str_to_elt(*mods))

    def add_post_modifier(self, *mods):
        """ Add one or more post-modifiers. """
        self._add_to_list(self.post_modifiers, *mods)

    def del_post_modifier(self, *mods):
        """ Delete one or more post-modifiers if present. """
        self._del_from_list(self.post_modifiers, *mods)

    def yield_post_modifiers(self):
        """ Iterate through pre-modifiers. """
        for o in self.post_modifiers:
            for x in o.constituents():
                yield x


#############################################################################
#
# Copyright (C) 2013 Roman Kutlak, University of Aberdeen.
# All rights reserved.
#
# This file is part of SAsSy NLG library.
#
# You may use this file under the terms of the BSD license as follows:
#
# "Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#   * Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in
#     the documentation and/or other materials provided with the
#     distribution.
#   * Neither the name of University of Aberdeen nor
#     the names of its contributors may be used to endorse or promote
#     products derived from this software without specific prior written
#     permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."
#
#############################################################################
