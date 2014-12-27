
import logging
from urllib.parse import quote_plus

from nlg.structures import *
import nlg.lexicon as lexicon


def get_log():
    return logging.getLogger(__name__)

get_log().addHandler(logging.NullHandler())


# functions for creating word elements

def noun(word):
    return Word(word, 'NOUN')

def verb(word):
    return Word(word, 'VERB')

def adjective(word):
    return Word(word, 'ADJECTIVE')

def adverb(word):
    return Word(word, 'ADVERB')

def pronoun(word):
    return Word(word, 'PRONOUN')

def preposition(word):
    return Word(word, 'PREPOSITION')

def conjunction(word):
    return Word(word, 'CONJUNCTION')

def determiner(word):
    return Word(word, 'DETERMINER')

def exclamation(word):
    return Word(word, 'EXCLAMATION')


# functions for creating phrases (mostly based on Penn Treebank tags)
# https://www.ling.upenn.edu/courses/Fall_2003/ling001/penn_treebank_pos.html
# scroll down for a list of tags

#12.	NN      Noun, singular or mass
#13.	NNS     Noun, plural
#14.	NNP     Proper noun, singular
#15.	NNPS	Proper noun, plural

def np(spec, head, features=None):
    return NP(noun(head), determiner(spec), features)

def nn(word):
    return noun(word)

def nns(word):
    o = noun(word)
    o.add_feature('NUMBER', 'PLURAL')
    return o

def nnp(name):
    o = noun(name)
    o.add_feature('PROPER', 'true')
    return o


# Visitors -- printing, realisation, etc.


class RealisationVisitor:
    """ A visitor that collects the strings in the NLG structure
    and performs a simple surface realisation.

    """
    def __init__(self):
        self.text = ''
    
    def __str__(self):
        tmp = self.text.replace(' ,', ',')
        tmp = tmp.split(' ')
        return ' '.join([x for x in tmp if x != '']).strip()

    def visit_element(self, node):
        pass
    
    def visit_string(self, node):
        self.text += node.val + ' '

    def visit_word(self, node):
        word = node.word
        if (node.get_feature('NUMBER') == 'PLURAL' and
            node.pos == 'NOUN'):
            word = lexicon.pluralise_noun(node.word)
        self.text += word + ' '

    def visit_placeholder(self, node):
        if node.value: node.value.accept(self)
        else: self.text += str(self.id)
        self.text += ' '

    def visit_clause(self, node):
        for o in node.pre_modifiers: o.accept(self)
        node.subj.accept(self)
        node.vp.accept(self)
        for o in node.post_modifiers: o.accept(self)
    
    def visit_coordination(self, node):
        if node.coords is None or len(node.coords) == 0: return ''
        if len(node.coords) == 1:
            node.coords[0].accept(self)
            return
        for i, x in enumerate(node.coords):
            x.accept(self)
            if node.conj == 'and' and i < len(node.coords) - 2:
                self.text += ', '
            elif i < len(node.coords) - 1:
                conj = node.conj
                if is_clause_t(self): conj = ', ' + node.conj
                self.text += ' ' + conj + ' '

    # FIXME: implement
    def visit_subordination(self, node):
        assert False, 'not implemented'
        if node.has_feature('COMPLEMENTISER'):
            self.text += ' ' + node.get_feature('COMPLEMENTISER')

    def visit_np(self, node):
        for c in node.front_modifiers: c.accept(self)
        node.spec.accept(self)
        for c in node.pre_modifiers: c.accept(self)
        node.head.accept(self)
        for c in node.complements: c.accept(self)
        for c in node.post_modifiers: c.accept(self)
    
    def visit_vp(self, node):
        for c in node.front_modifiers: c.accept(self)
        for c in node.pre_modifiers: c.accept(self)
        if str(node.head).strip() == 'have':
            if (node.has_feature('NEGATION') and
                node.get_feature('NEGATION') == 'TRUE'):
                self.text += 'do not have '
        elif str(node.head).strip() == 'has':
            if (node.has_feature('NEGATION') and
                node.get_feature('NEGATION') == 'TRUE'):
                self.text += 'does not have '
        else:
            node.head.accept(self)
            if (node.has_feature('NEGATION') and
                node.get_feature('NEGATION') == 'TRUE'):
                self.text += 'not '
        for c in node.complements: c.accept(self)
        for c in node.post_modifiers: c.accept(self)
    
    def visit_pp(self, node):
        self.visit_phrase(node)
    
    def visit_adjp(self, node):
        self.visit_phrase(node)
    
    def visit_advp(self, node):
        self.visit_phrase(node)

    def visit_phrase(self, node):
        for c in node.front_modifiers: c.accept(self)
        for c in node.pre_modifiers: c.accept(self)
        node.head.accept(self)
        for c in node.complements: c.accept(self)
        for c in node.post_modifiers: c.accept(self)


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
        text = ('{outer}<{tag} xsi:type="StringElement">{sep}'
                '{inner}<val>{val}</val>{sep}'
                '{outer}</{tag}>{sep}').format(val=quote_plus(str(node.val)),
                                              **self._get_args())
        self.xml += text

    def visit_word(self, node):
        tag = self.ancestors[-1]
        spaces = self.indent * self.depth
        # a bug in simplenlg treats 'is' differently from 'be'
        # so keep 'is' in templates to allow simple to_str realisation
        # but change it to 'be' for simplenlg
        word = node.word
        if word == 'is': word = 'be'
        features = node.features_to_xml_attributes()
        text = ('{outer}<{tag} xsi:type="WordElement" cat="{cat}"{f}>{sep}'
                '{inner}<base>{word}</base>{sep}'
                '{outer}</{tag}>{sep}').format(cat=quote_plus(str(node.pos)),
                                               word=quote_plus(str(word)),
                                               **self._get_args(f=features))
        self.xml += text

    def visit_placeholder(self, node):
        tag = self.ancestors[-1]
        spaces = self.indent * self.depth
        text = ('{outer}<{tag} xsi:type="StringElement">{sep}'
                '{inner}<val>{val}</val>{sep}'
                '{outer}</{tag}>{sep}').format(val=quote_plus(str(node.id)),
                                               **self._get_args())
        self.xml += text

    def visit_clause(self, node):
        tag = self.ancestors[-1]
        spaces = self.indent * self.depth
        features = node.features_to_xml_attributes()
        self.xml += '{outer}<{tag} xsi:type="SPhraseSpec"{f}>{sep}'\
                       .format(**self._get_args(f=features))
        self._process_elements(node, 'pre_modifiers', 'preMods')
        self._process_element(node, 'subj')
        self._process_element(node, 'vp')
        self._process_elements(node, 'post_modifiers', 'postMods')
        self.xml += '{outer}</{tag}>{sep}'.format(**self._get_args())

    def visit_np(self, node):
        tag = self.ancestors[-1]
        spaces = self.indent * self.depth
        features = node.features_to_xml_attributes()
        self.xml += '{outer}<{tag} xsi:type="NPPhraseSpec"{f}>{sep}'\
                       .format(**self._get_args(f=features))
        self._process_elements(node, 'front_modifiers', 'frontMods')
        self._process_elements(node, 'pre_modifiers', 'preMods')
        self._process_element(node, 'spec')
        self._process_element(node, 'head')
        self._process_elements(node, 'complements', 'compl')
        self._process_elements(node, 'post_modifiers', 'postMods')
        self.xml += '{outer}</{tag}>{sep}'.format(**self._get_args())

    def visit_phrase(self, node, type):
        tag = self.ancestors[-1]
        spaces = self.indent * self.depth
        features = node.features_to_xml_attributes()
        self.xml += '{outer}<{tag} xsi:type="{type}"{f}>{sep}'\
                       .format(type=type, **self._get_args(f=features))
        self._process_elements(node, 'front_modifiers', 'frontMods')
        self._process_elements(node, 'pre_modifiers', 'preMods')
        self._process_element(node, 'head')
        self._process_elements(node, 'complements', 'compl')
        self._process_elements(node, 'post_modifiers', 'postMods')
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
        tag = self.ancestors[-1]
        spaces = self.indent * self.depth
        features = node.features_to_xml_attributes()
        self.xml +='{outer}<{tag} xsi:type="CoordinatedPhraseElement"{f}>{sep}'\
                       .format(**self._get_args(f=features))
        self._process_elements(node, 'coords', 'coord')
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
    
    def spaces(self, n=-1):
        if n < 0: return ' ' * depth
        else: return ' ' * n
    
    def _process_elements(self, node, name):
        attr = getattr(node, name)
        if len(attr) == 0: return
        self.data += ',\n'
        if self.do_indent: self.data += self.indent
        self.indent += ' ' * len(name + '=[')
        self.data += name + '=['
        self.do_indent = False
        # don't print last comma
        i = len(attr) - 1
        for o in attr:
            i -= 1
            o.accept(self)
            self.do_indent = True
            if i > 0:
                self.data += ','
        self.data += ']'
        # restore the indent
        self.indent = self.indent[:-len(name + '=(')]
            
    def visit_element(self, node):
        pass
    
    def visit_string(self, node):
        if self.do_indent: self.data += self.indent
        self.data += 'String({0}'.format(repr(node.val))
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
        if node.value == Element():
            self.data += 'PlaceHolder({0}'.format(repr(node.id))
        else:
            self.data += 'PlaceHolder({0}, {1}'.format(repr(node.id),
                                                       repr(node.value))
        if node._features != dict():
            self.data += ', ' + repr(node._features)
        self.data += ')'

    def visit_np(self, node):
        if self.do_indent: self.data += self.indent
        self.data += 'NP('
        self.indent += ' ' * len('NP(')
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
        self.indent = self.indent[:-len('NP(')]
    
    def visit_phrase(self, node, name=''):
        if self.do_indent: self.data += self.indent
        self.indent += ' ' * len(name + '(')
        self.data += name + '('
        self.do_indent = False
        node.head.accept(self)
        self.do_indent = True
        i = len(node.complements)
        for c in node.complements:
            if i > 0:
                self.data += ',\n'
            i -= 1
            c.accept(self)
        if node._features != dict():
            self.data += ',\n'
            self.data += self.indent + 'features=' + repr(node._features)
        self._process_elements(node, 'front_modifiers')
        self._process_elements(node, 'pre_modifiers')
        self._process_elements(node, 'post_modifiers')
        self.data += ')'
        self.indent = self.indent[:-len(name + '(')]

    def visit_vp(self, node):
        self.visit_phrase(node, 'VP')

    def visit_pp(self, node):
        self.visit_phrase(node, 'PP')
    
    def visit_adjp(self, node):
        self.visit_phrase(node, 'AdjP')

    def visit_advp(self, node):
        self.visit_phrase(node, 'AdvP')
    
    def visit_clause(self, node):
        self.data += self.indent
        self.data += 'Clause('
        self.do_indent = False
        node.subj.accept(self)
        self.do_indent = True
        self.data += ',\n'
        self.indent += ' ' * len('Clause(')
        node.vp.accept(self)
        if node._features != dict():
            self.data += ',\n'
            self.data += self.indent + repr(node._features)
        self._process_elements(node, 'pre_modifiers')
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
    
    def visit_element(self, node):
        self.data += Element()
    
    def visit_string(self, node):
        if self.do_indent: self.data += self.indent
        self.data += 'String({0})'.format(repr(node.val))

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
        self.data += 'NP('
        self.indent += ' ' * len('NP(')
        self.do_indent = False
        node.head.accept(self)
        if node.spec != Element():
            self.data += ', '
            node.spec.accept(self)
        self.data += ')'
        self.do_indent = True
        self.indent = self.indent[:-len('NP(')]
    
    def visit_phrase(self, node, name=''):
        if self.do_indent: self.data += self.indent
        self.indent += ' ' * len(name + '(')
        self.data += name + '('
        self.do_indent = False
        node.head.accept(self)
        self.do_indent = True
        i = len(node.complements)
        for c in node.complements:
            if i > 0:
                self.data += ',\n'
            i -= 1
            c.accept(self)
        self.data += ')'
        self.indent = self.indent[:-len(name + '(')]

    def visit_vp(self, node):
        self.visit_phrase(node, 'VP')

    def visit_pp(self, node):
        self.visit_phrase(node, 'PP')
    
    def visit_adjp(self, node):
        self.visit_phrase(node, 'AdjP')

    def visit_advp(self, node):
        self.visit_phrase(node, 'AdvP')
    
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


# FIXME: no idea if the code below is used at all


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

        if isinstance(sent, NP):
            for x in sentence_iterator(sent.spec):
                yield x

        for o in reversed(sent.front_modifiers):
            for x in sentence_iterator(o):
                yield x

    if isinstance(sent, CC):
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

    if isinstance(sent, CC):
        for i, o in list(enumerate(sent.coords)):
            if (o == elt):
                if replacement is None:
                    del sent.coords[i]
                else:
                    sent.coords[i] = replacement
                return True

    if isinstance(sent, Phrase):
        res = False
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

        if isinstance(sent, NP):
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


# Penn Treebank Tags


#Number Tag    Description
#1.     CC      Coordinating conjunction
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
