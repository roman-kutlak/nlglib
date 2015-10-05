import logging
from urllib.parse import quote_plus

from .structures import Element, Word, Clause, Phrase, Coordination
from .structures import NounPhrase, VerbPhrase, PrepositionalPhrase
from .structures import AdjectivePhrase, AdverbPhrase, PlaceHolder
from .structures import is_clause_t, is_phrase_t, STRING, WORD
from .structures import NOUNPHRASE, VERBPHRASE, PLACEHOLDER, COORDINATION
from .lexicon import POS_VERB, POS_ADVERB

#from nlg.lexicon import POS_ANY, POS_ADJECTIVE, POS_ADVERB, POS_AUXILIARY
#from nlg.lexicon import POS_COMPLEMENTISER, POS_CONJUNCTION, POS_DETERMINER
#from nlg.lexicon import POS_MODAL, POS_NOUN, POS_NUMERAL, POS_PREPOSITION
#from nlg.lexicon import POS_PRONOUN, POS_SYMBOL, POS_VERB, POS_EXCLAMATION

def get_log():
    return logging.getLogger(__name__)

get_log().addHandler(logging.NullHandler())


#def template(word, lexicon, pos=POS_ANY):
#    """ Create syntactic template for expressing a word. """
#    assert False, "not implemented"


def promote_to_clause(e):
    """ Convert element into a clause. If it is a clause, return it as is. """
    if is_clause_t(e): return e
    if is_phrase_t(e):
        if e._type == NOUNPHRASE: return Clause(e)
        if e._type == VERBPHRASE: return Clause(Element(), e)
    return Clause(e)


def promote_to_phrase(e):
    """ Convert element into a clause. If it is a clause, return it as is. """
    if is_clause_t(e): return e
    if is_phrase_t(e): return e
    if e._type == STRING: return NounPhrase(e, features=e._features)
    if e._type == PLACEHOLDER: return NounPhrase(e, features=e._features)
    if e._type == WORD:
        if e.cat == POS_VERB: return VerbPhrase(e, features=e._features)
        if e.cat == POS_ADVERB: return VerbPhrase(e, features=e._features)
        return NounPhrase(e, features=e._features)
    if e._type == COORDINATION:
        return Coordination(*[promote_to_phrase(x) for x in e.coords],
                            conj=e.conj, features=e._features)
    return NounPhrase(e, features=e._features)



# Visitors -- printing, xml, etc.


class PrintVisitor:
    """ An abstract visitor class that maintains indentation info. """

    def __init__(self, depth = 0, indent='  ', sep='\n'):
        """ Initialise the depth, indent and separator info. """
        self.ancestors = []
        self.depth = depth
        self.indent = indent
        self.sep = sep

    def enter(self, tag):
        """ Increase the indentation level and set 'tag' as the ancestor. """
        self.ancestors.append(tag)
        self.depth += 1

    def exit(self):
        """ Decrease the indentation level and pop the last ancestor.
        Throws Exception if depth would be less than 0.

        """
        if len(self.ancestors) == 0:
            raise Exception('Attempting to exit an element at the top level')
        self.ancestors.pop()
        self.depth -= 1

    def _process_element(self, node, attr, name=None):
        """ Get the element of the node specified by attr and process it.
        Assumption: the element is an instance of Element.

        """
        if name is None: name = attr
        self.enter(name)
        e = getattr(node, attr)
        e.accept(self)
        self.exit()

    def _process_elements(self, node, attr, name):
        """ Get the list of elements of the node specified by attr
        and process them.

        """
        self.enter(name)
        elts = getattr(node, attr)
        for e in elts: e.accept(self)
        self.exit()

    def _get_args(self, **kwargs):
        args = {'tag': self.ancestors[-1],
                'outer': self.indent * self.depth,
                'inner': self.indent * (self.depth + 1),
                'sep'  : self.sep,
                }
        for k, v in kwargs.items(): args[k] = v
        return args

    def visit_element(self):
        pass


class XmlVisitor(PrintVisitor):
    """ Convert an NLG element structure into an XML readable by SimpleNLG. """

    header = '''\
<?xml version="1.0" encoding="utf-8"?>
<nlg:NLGSpec xmlns="http://simplenlg.googlecode.com/svn/trunk/res/xml"
xmlns:nlg="http://simplenlg.googlecode.com/svn/trunk/res/xml"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
xsi:schemaLocation="http://simplenlg.googlecode.com/svn/trunk/res/xml ">
<nlg:Request>

<Document cat="PARAGRAPH">
'''
    footer = '''
</Document>
</nlg:Request>
</nlg:NLGSpec>
'''

    def __init__(self, xml='', depth = 0, indent='  ', sep='\n'):
        super().__init__(depth, indent, sep)
        self.xml = xml
        self.ancestors.append('child')

    def visit_string(self, node):
        neg = 'not ' if node.has_feature('NEGATED', 'true') else ''
#        text = ('{outer}<{tag} xsi:type="StringElement">{sep}'
#                '{inner}<val>{neg}{val}</val>{sep}'
#                '{outer}</{tag}>{sep}').format(val=quote_plus(str(node.value)),
#                                               neg=neg, **self._get_args())
        features = node.features_to_xml_attributes()
        text = ('{outer}<{tag} xsi:type="WordElement" '
                'cat="ANY" canned="true" {f}>{sep}'
                '{inner}<base>{neg}{word}</base>{sep}'
                '{outer}</{tag}>{sep}').format(word=quote_plus(str(node.value)),
                                               neg=neg,
                                               **self._get_args(f=features))
        self.xml += text


    def visit_word(self, node):
        # a bug in simplenlg treats 'is' differently from 'be'
        # so keep 'is' in templates to allow simple to_str realisation
        # but change it to 'be' for simplenlg
        word = node.word
        if word == 'is': word = 'be'
        features = node.features_to_xml_attributes()
        text = ('{outer}<{tag} xsi:type="WordElement" {f}>{sep}'
                '{inner}<base>{word}</base>{sep}'
                '{outer}</{tag}>{sep}').format(word=quote_plus(str(word)),
                                               **self._get_args(f=features))
        self.xml += text

    def visit_placeholder(self, node):
        node.value.accept(self)

    def visit_clause(self, node):
        features = node.features_to_xml_attributes()
        self.xml += '{outer}<{tag} xsi:type="SPhraseSpec"{f}>{sep}'\
                       .format(**self._get_args(f=features))
        self._process_elements(node, 'front_modifiers', 'frontMod')
        self._process_element(node, 'subj')
        self._process_elements(node, 'pre_modifiers', 'preMod')
        self._process_element(node, 'vp')
        self._process_elements(node, 'complements', 'compl')
        self._process_elements(node, 'post_modifiers', 'postMod')
        self.xml += '{outer}</{tag}>{sep}'.format(**self._get_args())

    def visit_np(self, node):
        features = node.features_to_xml_attributes()
        self.xml += '{outer}<{tag} xsi:type="NPPhraseSpec"{f}>{sep}'\
                       .format(**self._get_args(f=features))
        self._process_elements(node, 'front_modifiers', 'frontMod')
        self._process_elements(node, 'pre_modifiers', 'preMod')
        self._process_element(node, 'spec')
        self._process_element(node, 'head')
        self._process_elements(node, 'complements', 'compl')
        self._process_elements(node, 'post_modifiers', 'postMod')
        self.xml += '{outer}</{tag}>{sep}'.format(**self._get_args())

    def visit_phrase(self, node, type):
        features = node.features_to_xml_attributes()
        self.xml += '{outer}<{tag} xsi:type="{type}"{f}>{sep}'\
                       .format(type=type, **self._get_args(f=features))
        self._process_elements(node, 'front_modifiers', 'frontMod')
        self._process_elements(node, 'pre_modifiers', 'preMod')
        self._process_element(node, 'head')
        self._process_elements(node, 'complements', 'compl')
        self._process_elements(node, 'post_modifiers', 'postMod')
        self.xml += '{outer}</{tag}>{sep}'.format(**self._get_args())

    def visit_vp(self, node):
        self.visit_phrase(node, 'VPPhraseSpec')

    def visit_pp(self, node):
        self.visit_phrase(node, 'PPPhraseSpec')

    def visit_adjp(self, node):
        self.visit_phrase(node, 'AdjPhraseSpec')

    def visit_advp(self, node):
        self.visit_phrase(node, 'AdvPhraseSpec')

    def visit_coordination(self, node):
        features = node.features_to_xml_attributes()
        self.xml +='{outer}<{tag} xsi:type="CoordinatedPhraseElement"{f}>{sep}'\
                       .format(**self._get_args(f=features))
        self._process_elements(node, 'pre_modifiers', 'preMod')
        self._process_elements(node, 'coords', 'coord')
        self._process_elements(node, 'complements', 'compl')
        self._process_elements(node, 'post_modifiers', 'postMod')
        self.xml += '{outer}</{tag}>{sep}'.format(**self._get_args())

    def visit_subordination(self, node):
        assert False, 'Not implemented'

    def to_xml(self):
        return (self.header + self.xml + self.footer).strip()

    def clear(self):
        self.xml = ''

    def __str__(self):
        return (self.to_xml())

    def __repr__(self):
        return 'XmlVisitor({0})'.format(self.xml)


class ReprVisitor(PrintVisitor):
    """ Create a string representation of an element and its subelements.
    The representation of an element should create the same element
    when passed to eval().

    """

    def __init__(self, data = '', depth = 0, indent='', sep=',\n'):
        super().__init__(depth, indent, sep)
        self.data = data
        self.do_indent = True

    def _process_elements(self, node, name):
        attr = getattr(node, name)
        if len(attr) == 0: return
        self.data += ',\n'
        if self.do_indent: self.data += self.indent
#        self.indent += ' ' * len(name + '=[')
        self.data += name + '=['
        def fn(x):
            if x is None: return
            r = ReprVisitor()
            x.accept(r)
            return str(r)
#        get_log().debug('*' * 4 + repr(attr))
        tmp = map(fn, attr)
        tmp_no_whites = [' '.join(x.split()) for x in tmp if x is not None]
        self.data += ', '.join(tmp_no_whites)
        self.data += ']'
        # restore the indent
#        self.indent = self.indent[:-len(name + '=(')]


    def visit_msg_spec(self, node):
        if self.do_indent: self.data += self.indent
        self.data += '{0}'.format(repr(node))

    def visit_element(self, node):
        if self.do_indent: self.data += self.indent
        self.data += 'Element()'

    def visit_string(self, node):
        if self.do_indent: self.data += self.indent
        self.data += 'String({0}'.format(repr(node.value))
        if node._features != dict():
            self.data += ', ' + repr(node._features)
        self.data += ')'

    def visit_word(self, node):
        if self.do_indent: self.data += self.indent
        self.data += 'Word({0}, {1}'.format(repr(node.word), repr(node.pos))
        if node._features != dict():
            self.data += ', ' + repr(node._features)
        self.data += ')'

    def visit_placeholder(self, node):
        if self.do_indent: self.data += self.indent
        if not node.value:
            self.data += 'PlaceHolder({0}'.format(repr(node.id))
        else:
            self.data += 'PlaceHolder({0}, {1}'.format(repr(node.id),
                                                       repr(node.value))
        if node._features != dict():
            self.data += ', ' + repr(node._features)
        self.data += ')'

    def visit_np(self, node):
        if self.do_indent: self.data += self.indent
        self.data += 'NounPhrase('
        self.indent += ' ' * len('NounPhrase(')
        self.do_indent = False
        node.head.accept(self)
        if node.spec != Element():
            self.data += ', '
            node.spec.accept(self)
        if node._features != dict():
            self.data += ', features=' + repr(node._features)
        self.do_indent = True
        self._process_elements(node, 'front_modifiers')
        self._process_elements(node, 'pre_modifiers')
        self._process_elements(node, 'complements')
        self._process_elements(node, 'post_modifiers')
        self.data += ')'
        self.indent = self.indent[:-len('NounPhrase(')]

    def visit_phrase(self, node, name=''):
        if self.do_indent: self.data += self.indent
        self.indent += ' ' * len(name + '(')
        self.data += name + '('
        if node.head:
            self.do_indent = False
            node.head.accept(self)
            self.do_indent = True
        else:
            self.do_indent = False
        i = len(node.complements)
        for c in node.complements:
            if i > 0:
                self.data += ',\n'
            i -= 1
            c.accept(self)
            self.do_indent = True
        if node._features != dict():
            self.data += ',\n'
            self.data += self.indent + 'features=' + repr(node._features)
        self._process_elements(node, 'front_modifiers')
        self._process_elements(node, 'pre_modifiers')
        self._process_elements(node, 'post_modifiers')
        self.data += ')'
        self.indent = self.indent[:-len(name + '(')]

    def visit_vp(self, node):
        self.visit_phrase(node, 'VerbPhrase')

    def visit_pp(self, node):
        self.visit_phrase(node, 'PrepositionalPhrase')

    def visit_adjp(self, node):
        self.visit_phrase(node, 'AdjectivePhrase')

    def visit_advp(self, node):
        self.visit_phrase(node, 'AdverbPhrase')

    def visit_clause(self, node):
        if self.do_indent: self.data += self.indent
        self.data += 'Clause('
        self.do_indent = False
        node.subj.accept(self)
        self.do_indent = True
        self.data += ',\n'
        self.indent += ' ' * len('Clause(')
        node.vp.accept(self)
        if node._features != dict():
            self.data += ',\n'
            self.data += self.indent + 'features=' + repr(node._features)
        self._process_elements(node, 'front_modifiers')
        self._process_elements(node, 'pre_modifiers')
        self._process_elements(node, 'complements')
        self._process_elements(node, 'post_modifiers')
        self.data += ')'
        self.indent = self.indent[:-len('Clause(')]

    def visit_coordination(self, node):
        if self.do_indent: self.data += self.indent
        self.data += 'Coordination('
        self.do_indent = False
        self.indent += ' ' * len('Coordination(')
        i = len(node.coords)
        for c in node.coords:
            i -= 1
            c.accept(self)
            self.data += ',\n'
            self.do_indent = True
        self.data += self.indent + 'conj={0}'.format(repr(node.conj))
        if node._features != dict():
            self.data += ',\n' + self.indent
            self.data += 'features=' + repr(node._features)
        self.do_indent = True
        self.data += ')'
        self.indent = self.indent[:-len('Coordination(')]

    def clear(self):
        self.data = ''

    def not_indented_str(self):
        """ Return the representation on a single line instead of indented. """
        return ' '.join(str(self).split())

    def __str__(self):
        return self.data.strip()

    def __repr__(self):
        return 'ReprVisitor({0})'.format(self.data)


class StrVisitor(PrintVisitor):
    """ Create a string representation of an element and its subelements.
    The representation shows only the basic info (no features, mods, etc).

    """

    def __init__(self, data = '', depth = 0, indent='', sep=',\n'):
        super().__init__(depth, indent, sep)
        self.data = data
        self.do_indent = True

    def visit_msg_spec(self, node):
        if self.do_indent: self.data += self.indent
        self.data += '{0}'.format(node)

    def visit_element(self, node):
        self.data += ''

    def visit_string(self, node):
        if self.do_indent: self.data += self.indent
        self.data += 'String({0})'.format(repr(node.value))

    def visit_word(self, node):
        if self.do_indent: self.data += self.indent
        self.data += 'Word({0}, {1})'.format(repr(node.word), repr(node.pos))

    def visit_placeholder(self, node):
        if self.do_indent: self.data += self.indent
        if node.value == Element():
            self.data += 'PlaceHolder({0})'.format(repr(node.id))
        else:
            self.data += 'PlaceHolder({0}, {1})'.format(repr(node.id),
                                                        repr(node.value))

    def visit_np(self, node):
        if self.do_indent: self.data += self.indent
        self.data += 'NounPhrase('
        self.indent += ' ' * len('NounPhrase(')
        self.do_indent = False
        node.head.accept(self)
        if node.spec != Element():
            self.data += ', '
            node.spec.accept(self)
        self.data += ')'
        self.do_indent = True
        self.indent = self.indent[:-len('NounPhrase(')]

    def visit_phrase(self, node, name=''):
        if self.do_indent: self.data += self.indent
        self.indent += ' ' * len(name + '(')
        self.data += name + '('
        if node.head:
            self.do_indent = False
            node.head.accept(self)
            self.do_indent = True
        else:
            self.do_indent = False
        i = len(node.complements)
        for c in node.complements:
            if i > 0:
                self.data += ',\n'
            i -= 1
            c.accept(self)
            self.do_indent = True
        self.data += ')'
        self.indent = self.indent[:-len(name + '(')]

    def visit_vp(self, node):
        self.visit_phrase(node, 'VerbPhrase')

    def visit_pp(self, node):
        self.visit_phrase(node, 'PrepositionalPhrase')

    def visit_adjp(self, node):
        self.visit_phrase(node, 'AdjectivePhrase')

    def visit_advp(self, node):
        self.visit_phrase(node, 'AdverbPhrase')

    def visit_clause(self, node):
        self.data += self.indent
        self.data += 'Clause('
        self.do_indent = False
        node.subj.accept(self)
        self.do_indent = True
        self.data += ',\n'
        self.indent += ' ' * len('Clause(')
        node.vp.accept(self)
        self.data += ')'
        self.indent = self.indent[:-len('Clause(')]

    def visit_coordination(self, node):
        if self.do_indent: self.data += self.indent
        self.data += 'Coordination('
        self.do_indent = False
        self.indent += ' ' * len('Coordination(')
        i = len(node.coords)
        for c in node.coords:
            i -= 1
            c.accept(self)
            self.data += ',\n'
            self.do_indent = True
        self.data += self.indent + 'conj={0}'.format(repr(node.conj))
        self.do_indent = True
        self.data += ')'
        self.indent = self.indent[:-len('Coordination(')]

    def clear(self):
        self.data = ''

    def __str__(self):
        return self.data.strip()

    def __repr__(self):
        return 'StrVisitor({0})'.format(self.data)


class ElementVisitor:
    """ This visitor collects all leaf elements of a syntax tree. """

    def __init__(self):
        self.elements = []

    def _process_elements(self, node, name):
        attr = getattr(node, name)
        for o in attr:
            o.accept(self)

    def _process_element(self, node, name):
        o = getattr(node, name)
        o.accept(self)

    def visit_element(self):
        pass

    def visit_string(self, node):
        self.elements.append(node)

    def visit_word(self, node):
        self.elements.append(node)

    def visit_placeholder(self, node):
        self.elements.append(node)

    def visit_np(self, node):
        self._process_elements(node, 'front_modifiers')
        self._process_element(node, 'spec')
        self._process_elements(node, 'pre_modifiers')
        self._process_element(node, 'head')
        self._process_elements(node, 'complements')
        self._process_elements(node, 'post_modifiers')

    def visit_phrase(self, node):
        self._process_elements(node, 'front_modifiers')
        self._process_elements(node, 'pre_modifiers')
        self._process_element(node, 'head')
        self._process_elements(node, 'complements')
        self._process_elements(node, 'post_modifiers')

    def visit_vp(self, node):
        self.visit_phrase(node)

    def visit_pp(self, node):
        self.visit_phrase(node)

    def visit_adjp(self, node):
        self.visit_phrase(node)

    def visit_advp(self, node):
        self.visit_phrase(node)

    def visit_coordination(self, node):
        self._process_elements(node, 'coords')


class ConstituentVisitor:
    """ This visitor collects all elements of a syntax tree. """

    def __init__(self):
        self.elements = []

    def _process_elements(self, node, name):
        attr = getattr(node, name)
        for o in attr:
            o.accept(self)

    def _process_element(self, node, name):
        o = getattr(node, name)
        o.accept(self)

    def visit_element(self):
        pass

    def visit_string(self, node):
        self.elements.append(node)

    def visit_word(self, node):
        self.elements.append(node)

    def visit_placeholder(self, node):
        self.elements.append(node)

    def visit_np(self, node):
        self.elements.append(self)
        self._process_elements(node, 'front_modifiers')
        self._process_element(node, 'spec')
        self._process_elements(node, 'pre_modifiers')
        self._process_element(node, 'head')
        self._process_elements(node, 'complements')
        self._process_elements(node, 'post_modifiers')

    def visit_phrase(self, node):
        self.elements.append(self)
        self._process_elements(node, 'front_modifiers')
        self._process_elements(node, 'pre_modifiers')
        self._process_element(node, 'head')
        self._process_elements(node, 'complements')
        self._process_elements(node, 'post_modifiers')

    def visit_vp(self, node):
        self.visit_phrase(node)

    def visit_pp(self, node):
        self.visit_phrase(node)

    def visit_adjp(self, node):
        self.visit_phrase(node)

    def visit_advp(self, node):
        self.visit_phrase(node)

    def visit_coordination(self, node):
        self.elements.append(self)
        self._process_elements(node, 'coords')


def sentence_iterator(sent):
    if isinstance(sent, Clause):
        for x in sentence_iterator(sent.vp):
            yield x
        yield sent.vp
        yield sent.subj

        return

    if isinstance(sent, Phrase):
        for o in reversed(sent.post_modifiers):
            for x in sentence_iterator(o):
                yield x

        for o in reversed(sent.complements):
            for x in sentence_iterator(o):
                yield x

        if sent.head is not None:
            for x in sentence_iterator(sent.head):
                yield x

        for o in reversed(sent.pre_modifiers):
            for x in sentence_iterator(o):
                yield x

        if isinstance(sent, NounPhrase):
            for x in sentence_iterator(sent.spec):
                yield x

        for o in reversed(sent.front_modifiers):
            for x in sentence_iterator(o):
                yield x

    if isinstance(sent, Coordination):
        for x in sent.coords:
            yield x
        yield sent

    else:
        yield (sent)


def aggregation_sentence_iterator(sent):
    if isinstance(sent, Clause):
        for x in sentence_iterator(sent.vp):
            yield x
        return

    if isinstance(sent, Phrase):
        for o in reversed(sent.post_modifiers):
            for x in sentence_iterator(o):
                yield x

    for o in reversed(sent.complements):
        for x in sentence_iterator(o):
            yield x

    for o in reversed(sent.pre_modifiers):
        for x in sentence_iterator(o):
            yield x

    else:
        yield (sent)


# TODO: find out if it is used and probably deprecate
def replace_element(sent, elt, replacement=None):
    if sent == elt:
        return True

    if isinstance(sent, Clause):
        if sent.subj == elt:
            sent.subj = replacement
            return True
        else:
            if replace_element(sent.subj, elt, replacement):
                return True;

        if sent.vp == elt:
            sent.vp = replacement
            return True

        else:
            if replace_element(sent.vp, elt, replacement):
                return True;

    if isinstance(sent, Coordination):
        for i, o in list(enumerate(sent.coords)):
            if (o == elt):
                if replacement is None:
                    del sent.coords[i]
                else:
                    sent.coords[i] = replacement
                return True
            else:
                if replace_element(o, elt, replacement):
                    return True

    if isinstance(sent, Phrase):
        for i, o in reversed(list(enumerate(sent.post_modifiers))):
            if (o == elt):
                if replacement is None:
                    del sent.post_modifiers[i]
                else:
                    sent.post_modifiers[i] = replacement
                return True
            else:
                if replace_element(o, elt, replacement):
                    return True
        for i, o in reversed(list(enumerate(sent.complements))):
            if (o == elt):
                if replacement is None:
                    del sent.complements[i]
                else:
                    sent.complements[i] = replacement
                return True
            else:
                if replace_element(o, elt, replacement):
                    return True
        if sent.head == elt:
            sent.head = replacement
            return True
        for i, o in reversed(list(enumerate(sent.pre_modifiers))):
            if (o == elt):
                if replacement is None:
                    del sent.pre_modifiers[i]
                else:
                    sent.pre_modifiers[i] = replacement
                return True
            else:
                if replace_element(o, elt, replacement):
                    return True

        if isinstance(sent, NounPhrase):
            if sent.spec == elt:
                sent.spec = replacement
                return True

        for i, o in reversed(list(enumerate(sent.front_modifiers))):
            if (o == elt):
                if replacement is None:
                    del sent.front_modifiers[i]
                else:
                    sent.front_modifiers[i] = replacement
                return True
            else:
                if replace_element(o, elt, replacement):
                    return True
    return False


def replace_element_with_id(sent, elt_id, replacement=None):
    if id(sent) == elt_id:
        return True

    if isinstance(sent, Coordination):
        for i, o in list(enumerate(sent.coords)):
            if (id(o) == elt_id):
                if replacement is None:
                    del sent.coords[i]
                else:
                    sent.coords[i] = replacement
                return True
            else:
                if replace_element_with_id(o, elt_id, replacement):
                    return True

    if isinstance(sent, Clause):
        for i, o in reversed(list(enumerate(sent.pre_modifiers))):
            if (id(o) == elt_id):
                if replacement is None:
                    del sent.pre_modifiers[i]
                else:
                    sent.pre_modifiers[i] = replacement
                return True
            else:
                if replace_element_with_id(o, elt_id, replacement):
                    return True

        if id(sent.subj) == elt_id:
            sent.subj = replacement or Element()
            return True
        else:
            if replace_element_with_id(sent.subj, elt_id, replacement):
                return True;

        if id(sent.vp) == elt_id:
            sent.vp = replacement
            return True

        else:
            if replace_element_with_id(sent.vp, elt_id, replacement):
                return True;

        for i, o in reversed(list(enumerate(sent.complements))):
            if (id(o) == elt_id):
                if replacement is None:
                    del sent.complements[i]
                else:
                    sent.complements[i] = replacement
                return True
            else:
                if replace_element_with_id(o, elt_id, replacement):
                    return True

        for i, o in reversed(list(enumerate(sent.post_modifiers))):
            if (id(o) == elt_id):
                if replacement is None:
                    del sent.post_modifiers[i]
                else:
                    sent.post_modifiers[i] = replacement
                return True
            else:
                if replace_element_with_id(o, elt_id, replacement):
                    return True

    if isinstance(sent, Phrase):
        for i, o in reversed(list(enumerate(sent.post_modifiers))):
            if (id(o) == elt_id):
                if replacement is None:
                    del sent.post_modifiers[i]
                else:
                    sent.post_modifiers[i] = replacement
                return True
            else:
                if replace_element_with_id(o, elt_id, replacement):
                    return True
        for i, o in reversed(list(enumerate(sent.complements))):
            if (id(o) == elt_id):
                if replacement is None:
                    del sent.complements[i]
                else:
                    sent.complements[i] = replacement
                return True
            else:
                if replace_element_with_id(o, elt_id, replacement):
                    return True
        if id(sent.head) == elt_id:
            sent.head = replacement
            return True
        for i, o in reversed(list(enumerate(sent.pre_modifiers))):
            if (id(o) == elt_id):
                if replacement is None:
                    del sent.pre_modifiers[i]
                else:
                    sent.pre_modifiers[i] = replacement
                return True
            else:
                if replace_element_with_id(o, elt_id, replacement):
                    return True

        if isinstance(sent, NounPhrase):
            if (sent.spec) == elt_id:
                sent.spec = replacement
                return True

        for i, o in reversed(list(enumerate(sent.front_modifiers))):
            if (id(o) == elt_id):
                if replacement is None:
                    del sent.front_modifiers[i]
                else:
                    sent.front_modifiers[i] = replacement
                return True
            else:
                if replace_element_with_id(o, elt_id, replacement):
                    return True
    return False



# Penn Treebank Tags


#Number Tag    Description
#1.     Coordination      Coordinating conjunction
#2.     CD      Cardinal number
#3.     DT      Determiner
#4.     EX      Existential there
#5.     FW      Foreign word
#6.     IN      Preposition or subordinating conjunction
#7.     JJ      Adjective
#8.     JJR     Adjective, comparative
#9.     JJS     Adjective, superlative
#10.	LS      List item marker
#11.	MD      Modal
#12.	NN      Noun, singular or mass
#13.	NNS     Noun, plural
#14.	NNP     Proper noun, singular
#15.	NNPS	Proper noun, plural
#16.	PDT     Predeterminer
#17.	POS     Possessive ending
#18.	PRP     Personal pronoun
#19.	PRP$	Possessive pronoun
#20.	RB      Adverb
#21.	RBR     Adverb, comparative
#22.	RBS     Adverb, superlative
#23.	RP      Particle
#24.	SYM     Symbol
#25.	TO      to
#26.	UH      Interjection
#27.	VB      Verb, base form
#28.	VBD     Verb, past tense
#29.	VBG     Verb, gerund or present participle
#30.	VBN     Verb, past participle
#31.	VBP     Verb, non-3rd person singular present
#32.	VBZ     Verb, 3rd person singular present
#33.	WDT     Wh-determiner
#34.	WP      Wh-pronoun
#35.	WP$	    Possessive wh-pronoun
#36.	WRB     Wh-adverb


#############################################################################
##
## Copyright (C) 2014 Roman Kutlak, University of Aberdeen.
## All rights reserved.
##
## This file is part of SAsSy NLG library.
##
## You may use this file under the terms of the BSD license as follows:
##
## "Redistribution and use in source and binary forms, with or without
## modification, are permitted provided that the following conditions are
## met:
##   * Redistributions of source code must retain the above copyright
##     notice, this list of conditions and the following disclaimer.
##   * Redistributions in binary form must reproduce the above copyright
##     notice, this list of conditions and the following disclaimer in
##     the documentation and/or other materials provided with the
##     distribution.
##   * Neither the name of University of Aberdeen nor
##     the names of its contributors may be used to endorse or promote
##     products derived from this software without specific prior written
##     permission.
##
## THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
## "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
## LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
## A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
## OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
## SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
## LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
## DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
## THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
## (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
## OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."
##
#############################################################################
