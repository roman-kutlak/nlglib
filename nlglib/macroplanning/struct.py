import inspect

from nlglib.features import category, NEGATED
from nlglib.microplanning import String, Element


class SignatureError(Exception):
    """Exception for PredicateMsgSpec."""
    pass


class Document:
    """Document represents a container holding information about a document.

    This includes the document title and a list of sections. The title
    and the sections can be also `Document` instances. For convenience,
    if you pass in `str`, it will be promoted to `String`. 
    Any other types are left as they are.

    """

    category = category.DOCUMENT

    def __init__(self, title, *sections):
        """Create a new `Document` with `title` and zero or more `sections`.

        :param title: the tile of the document (`Document` or `Element` type)
        :param sections: document sections (`Document` or `Element` type)

        """
        self._title = promote_to_string(title)
        self._sections = [promote_to_string(s) for s in sections]

    def __eq__(self, other):
        return (isinstance(other, Document) and
                other.category == self.category and
                self.title == other.title and
                self.sections == other.sections)

    def __hash__(self):
        return hash(str(self))

    def __repr__(self):
        title = self.title if self.title is not None else 'No title'
        sections = '\n'.join(repr(s) for s in self.sections)
        return '<Document: ({})\n{}>'.format(title, sections)

    def __str__(self):
        if self.title:
            return (str(self.title) + '\n\n' +
                    '\n\n'.join([str(s) for s in self.sections]))
        else:
            return '\n\n'.join([str(s) for s in self.sections])

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value):
        self._title = promote_to_string(value)

    @property
    def sections(self):
        return self._sections

    @sections.setter
    def sections(self, *sections):
        self._sections = [promote_to_string(s) for s in sections]

    def elements(self, recursive=False, itself=None):
        """ Return a generator to iterate through the elements. """
        if self.title is not None:
            if recursive:
                yield from self.title.elements(recursive, itself)
            else:
                yield self.title
        for s in self.sections:
            if recursive:
                yield from s.elements(recursive, itself)
            else:
                yield s

    # TODO: use visitor and match with simplenlg?
    def to_xml(self, depth=0, indent='  '):
        """Return an XML representation of the document"

        :param depth: the initial indentation offset (depth * indent)
        :param indent: the indent for nested elements.
        """
        offset = indent * depth
        result = offset + '<document>\n'
        result += offset + indent + '<title>\n'
        result += self.title.to_xml(depth=depth + 1)
        result += offset + indent + '</title>\n'
        result += offset + indent + '<sections>\n'
        for s in self.sections:
            result += s.to_xml(depth=depth + 1)
        result += offset + indent + '</sections>\n'
        result += offset + '</document>\n'
        return result


class Paragraph:
    """Paragraph represents a container holding sentences.

    For convenience, if you pass in `str`, it will be promoted to `String`.
    Any other types are left as they are.

    """

    category = category.PARAGRAPH

    def __init__(self, *sentences):
        """Create a new `Paragraph` with zero or more `sentences`.

        :param sentences: document sections (`RhetRel` or `Element` type)

        """
        self._sentences = [promote_to_string(s) for s in sentences]

    def __eq__(self, other):
        return (isinstance(other, Paragraph) and
                other.category == self.category and
                self.sentences == other.sentences)

    def __hash__(self):
        return hash(str(self))

    def __repr__(self):
        sentences = '\n\t'.join(repr(s) for s in self.sentences)
        return '<Paragraph ({}):\n\t{}>'.format(len(self.sentences), sentences)

    def __str__(self):
        return ' '.join([str(s) for s in self.sentences]).strip()

    @property
    def sentences(self):
        return self._sentences

    @sentences.setter
    def sentences(self, *sentences):
        self._sentences = [promote_to_string(s) for s in sentences]

    def elements(self, recursive=False, itself=None):
        """ Return a generator to iterate through the elements. """
        for s in self.sentences:
            if recursive:
                yield from s.elements(recursive, itself)
            else:
                yield s

    # TODO: use visitor and match with simplenlg?
    def to_xml(self, depth=0, indent='  '):
        """Return an XML representation of the document"

        :param depth: the initial indentation offset (depth * indent)
        :param indent: the indent for nested elements.
        """
        offset = indent * depth
        result = offset + '<paragraph>\n'
        result += offset + indent + '<sentences>\n'
        for s in self.sentences:
            result += s.to_xml(depth=depth + 1)
        result += offset + indent + '</sentences>\n'
        result += offset + '</paragraph>\n'
        return result


class RhetRel:
    """ A representation of a rhetorical relation (RST).

    The data structure is from RAGS (Mellish et. al. 2006) and it represents
    an element in the rhetorical structure of the document. Each element has
    a nuclei, a satellite and a relation name. Some relations allow multiple
    nuclei instead of a satellite (e.g., lists).

    Rhetorical relation is a tree. The children can be either `RhetRel`s
    or `MsgSpec`s.

    """

    category = category.RST
    phrases = ['']
    element_order = ['nucleus', 'satellite']
    is_abstract = True  # subclasses should override this
    # TODO: define RST_RELATIONS (abstract + concrete)?

    def __init__(self, relation, *nuclei, satellite=None, features=None,
                 marker=None, last_element_marker=None):
        if not nuclei:
            raise ValueError('At least one nucleus required for a RhetRel.')
        self.relation = relation
        self.nuclei = [promote_to_string(n) for n in nuclei]
        self.satellite = promote_to_string(satellite)
        self.marker = marker or self.phrases[0]
        self.last_element_marker = last_element_marker or self.marker
        self.features = features or {}
        self.is_multinuclear = len(self.nuclei) > 1
        if self.is_multinuclear:
            self.order = self.nuclei
        else:
            # e.g., [self.nucleus, self.satellite]
            self.order = [getattr(self, attr) for attr in self.element_order]

    def __repr__(self):
        elements = ' '.join(repr(x) for x in self.order)
        return '<RhetRel ({}): {}>'.format(self.relation, elements)

    def __str__(self):
        return ' '.join(str(x) for x in self.order)

    def __eq__(self, other):
        return (other.category == self.category and
                self.relation == other.relation and
                self.nuclei == other.nuclei and
                self.satellite == other.satellite and
                self.marker == other.marker)

    def __hash__(self):
        return hash(str(self))

    @property
    def nucleus(self):
        return self.nuclei[0]

    def elements(self, recursive=False, itself=None):
        for x in self.order:
            yield from x.elements(recursive, itself)

    def to_xml(self, lvl=0, indent='  '):
        spaces = indent * lvl
        data = spaces + '<RhetRel name="' + self.relation + '">\n'
        data += indent + spaces + '<marker>' + self.marker + '</marker>\n'
        data += indent + spaces + '<nuclei>\n'
        data += indent * 2 + spaces + '<nucleus>\n'
        for n in self.nuclei:
            data += n.to_xml(lvl + 3) + '\n'
        data += indent * 2 + spaces + '</nucleus>\n'
        data += indent * 2 + spaces + '<satellite>\n'
        data += self.satellite.to_xml(lvl + 3)
        data += indent * 2 + spaces + '</satellite>\n'
        data += spaces + '</RhetRel>\n'
        return data

    def to_str(self):
        if self.is_multinuclear:
            strings = [n.to_str() for n in self.nuclei]
            rv = strings[0]
            for i, s in enumerate(strings[1:]):
                if i < len(strings) - 2:
                    rv = ' '.join([rv, self.marker, s])
                else:
                    rv = ' '.join([rv, self.last_element_marker, s])
        else:
            rv = ' '.join([self.order[0].to_str(),
                           self.marker,
                           self.order[1].to_str()])
        rv = rv.replace(' , ', ', ').replace('  ', ' ')
        return rv


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

    category = category.MSG

    def __init__(self, name, features=None):
        self.name = name
        self.features = features or {}

    def __repr__(self):
        return 'MsgSpec({0}, {1})'.format(self.name, self.features)

    def __str__(self):
        return str(self.name)

    def __eq__(self, other):
        return (other.category == self.category and
                self.name == other.name)

    @property
    def id(self):
        return self.name

    def value_for(self, attr):
        """ Return a value for an argument using introspection. """
        if not hasattr(self, attr):
            raise ValueError('Error: cannot find value for key: %s' % attr)
        m = getattr(self, attr)
        if not hasattr(m, '__call__'):
            raise ValueError('Error: cannot call the method "%s"' % attr)
        return m()

    # TODO: extract to `Visitable` mixin class
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

    def elements(self, recursive=False, itself=None):
        if recursive or itself:
            yield self


class StringMsg(MsgSpec):
    """ Use this as a simple message that contains canned text. """

    def __init__(self, text):
        super().__init__('string_message_spec')
        self.text = str(text)

    def __str__(self):
        return self.text

    def value_for(self, _):
        return String(self.text)

    def to_xml(self, offset='', indent='  '):
        """Return an XML representation of the paragraph indented by initial ``offset``"
        :param offset: the initial offset
        :param indent: the indent for nested elements.
        """
        result = offset + '<msgspec template_name="{}">\n'.format(self.name)
        result += offset + indent + '<text>{}</text>\n'.format(self.text)
        result += offset + '</msgspec>\n'
        return result


class PredicateMsg(MsgSpec):
    """ This class is used for instantiating Predicate as message spec. """

    def __init__(self, pred, *arguments, features=None):
        """Representation of a predicate.
        
        :param pred: `nltk.sem.ApplicationExpression` instance
        
        """
        super().__init__(pred, features=features)
        self.args = list(arguments)

    def __str__(self):
        """ Return a suitable string representation. """
        if len(self.args) == 0:
            return self.name
        else:
            return self.name + '(' + ', '.join([str(x) for x in self.args]) + ')'

    def __repr__(self):
        """ Return a suitable string representation. """
        if len(self.args) == 0:
            return self.name
        else:
            neg = ''
            if NEGATED.true in self.features:
                neg = '-'
            return neg + self.name + '(' + ', '.join([str(x) for x in self.args]) + ')'

    def value_for(self, key):
        """Return a replacement for a var with argument number or key.
        
        `value_for(0)` will return predicate argument 0
        `value_for('foo')` will return self.foo

        """
        try:
            idx = int(key)
        except ValueError:
            return super().value_for(key)
        if idx >= len(self.args):
            msg = ('Requested index ({}) is larger than '
                   'the number of variables in the predicate "{}"')
            raise SignatureError(msg.format(idx, repr(self)))
        return self.args[idx]


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


def promote_to_string(s):
    """Convert non-nlglib classes (e.g., str) to String and return."""
    if not s:
        return String('')
    if isinstance(s, (Document, Element, RhetRel, MsgSpec)):
        return s
    return String(s)
