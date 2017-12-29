from urllib.parse import quote_plus

from nlglib.features import DISCOURSE_FUNCTION, ASPECT, category, FeatureGroup
from nlglib.features import NON_COMPARABLE_FEATURES
from .struct import Element, Word, String, Clause, Phrase, Coordination, NounPhrase


class PrintVisitor:
    """ An abstract visitor class that maintains indentation info. """

    def __init__(self, depth=0, indent='  ', sep='\n'):
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
                'sep': self.sep,
                }
        for k, v in kwargs.items(): args[k] = v
        return args


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

    def __init__(self, xml='', depth=0, indent='  ', sep='\n'):
        super(XmlVisitor, self).__init__(depth, indent, sep)
        self.xml = xml
        self.ancestors.append('child')

    def element(self, _):
        pass

    def string(self, node):
        # neg = 'not ' if node.negated == 'true' else ''
        neg = ''
        features = self.features_to_xml_attributes(node)
        text = ('{outer}<{tag} xsi:type="WordElement" '
                'canned="true" {f}>{sep}'
                '{inner}<base>{neg}{word}</base>{sep}'
                '{outer}</{tag}>{sep}').format(word=quote_plus(node.value),
                                               neg=neg,
                                               **self._get_args(f=features))
        self.xml += text

    def word(self, node):
        # a bug in simplenlg treats 'is' differently from 'be'
        # so keep 'is' in templates to allow simple to_str realisation
        # but change it to 'be' for simplenlg
        word = node.word
        if word == 'is': word = 'be'
        features = self.features_to_xml_attributes(node)
        id = ' id="{}"'.format(node.id) if node.id else ''
        text = ('{outer}<{tag} xsi:type="WordElement"{f}{id}>{sep}'
                '{inner}<base>{word}</base>{sep}'
                '{outer}</{tag}>{sep}').format(word=quote_plus(word), id=id,
                                               **self._get_args(f=features))
        self.xml += text

    def var(self, node):
        node.value.accept(self)

    def clause(self, node):
        features = self.features_to_xml_attributes(node)
        self.xml += '{outer}<{tag} xsi:type="SPhraseSpec"{f}>{sep}' \
            .format(**self._get_args(f=features))
        self._process_elements(node, 'front_modifiers', name='frontMod')
        self._process_element(node, 'subject', name='subj')
        self._process_elements(node, 'premodifiers', name='preMod')
        self._process_element(node, 'predicate', name='vp')
        self._process_elements(node, 'complements', name='compl')
        self._process_elements(node, 'postmodifiers', name='postMod')
        self.xml += '{outer}</{tag}>{sep}'.format(**self._get_args())

    def noun_phrase(self, node):
        features = self.features_to_xml_attributes(node)
        self.xml += '{outer}<{tag} xsi:type="NPPhraseSpec"{f}>{sep}' \
            .format(**self._get_args(f=features))
        self._process_element(node, 'specifier', 'spec')
        self._process_elements(node, 'premodifiers', 'preMod')
        self._process_element(node, 'head')
        self._process_elements(node, 'complements', 'compl')
        self._process_elements(node, 'postmodifiers', 'postMod')
        self.xml += '{outer}</{tag}>{sep}'.format(**self._get_args())

    def phrase(self, node, typ):
        features = self.features_to_xml_attributes(node)
        self.xml += '{outer}<{tag} xsi:type="{type}"{f}>{sep}' \
            .format(type=typ, **self._get_args(f=features))
        self._process_elements(node, 'premodifiers', 'preMod')
        self._process_element(node, 'head')
        self._process_elements(node, 'complements', 'compl')
        self._process_elements(node, 'postmodifiers', 'postMod')
        self.xml += '{outer}</{tag}>{sep}'.format(**self._get_args())

    def verb_phrase(self, node):
        self.phrase(node, 'VPPhraseSpec')

    def preposition_phrase(self, node):
        self.phrase(node, 'PPPhraseSpec')

    def adjective_phrase(self, node):
        self.phrase(node, 'AdjPhraseSpec')

    def adverb_phrase(self, node):
        self.phrase(node, 'AdvPhraseSpec')

    def coordination(self, node):
        features = self.features_to_xml_attributes(node)
        self.xml += '{outer}<{tag} xsi:type="CoordinatedPhraseElement"{f} conj="{conj}">{sep}' \
            .format(conj=str(node.conj), **self._get_args(f=features))
        self._process_elements(node, 'coords', 'coord')
        self.xml += '{outer}</{tag}>{sep}'.format(**self._get_args())

    def to_xml(self):
        return (self.header + self.xml + self.footer).strip()

    def clear(self):
        self.xml = ''

    def __str__(self):
        return self.to_xml()

    def __repr__(self):
        return 'XmlVisitor({0})'.format(self.xml)

    @staticmethod
    def features_to_xml_attributes(element, feature_map=None):
        features = ""
        feature_map = simplenlg_features if feature_map is None else feature_map
        if isinstance(element, Word):
            cat = element.pos
        elif isinstance(element, String):
            cat = category.ANY
        else:
            cat = element.category
        features_dict = {
            'cat': cat
        }
        for f in element.features:
            # if feature or feature group is not in dict, just return a dict with K:V
            value = f.value.lower()
            default_value = value if value in ('true', 'false') else f.value.upper()
            converted = feature_map.get(f, {
                f.name.upper(): default_value
            })
            # returned value is either a dict or a lambda taking `f`
            if hasattr(converted, '__call__'):
                converted = converted(f)
            features_dict.update(converted)
        if features_dict:
            for k in sorted(features_dict.keys()):
                features += '%s="%s" ' % (quote_plus(str(k)), quote_plus(str(features_dict[k])))
            return ' ' + features.strip()
        return ''


# either a dict or a lambda taking Feature and returning a dict
simplenlg_features = {
    DISCOURSE_FUNCTION: lambda f: {'discourseFunction': f.value},
    ASPECT.progressive: {'PROGRESSIVE': 'true'},
    ASPECT.perfect: {'PERFECT': 'true'},
    ASPECT.perfect_progressive: {'PERFECT': 'true',
                                 'PROGRESSIVE': 'true'},
    FeatureGroup('conj'): lambda f: {f.name: f.value},
    FeatureGroup('complementiser'): lambda f: {f.name.upper(): f.value},
    FeatureGroup('COMPLEMENTISER'): lambda f: {f.name: f.value},
}


class ReprVisitor(PrintVisitor):
    """ Create a string representation of an element and its subelements.
    The representation of an element should create the same element
    when passed to eval().

    """

    def __init__(self, data='', depth=0, indent='', sep=',\n'):
        super(ReprVisitor, self).__init__(depth, indent, sep)
        self.data = data
        self.do_indent = True

    def _process_elements(self, node, name, _=None):
        attr = getattr(node, name)
        if len(attr) == 0: return
        self.data += ',\n'
        if self.do_indent: self.data += self.indent
        self.data += name + '=['

        def fn(x):
            if x is None: return
            r = ReprVisitor()
            x.accept(r)
            return str(r)

        tmp = map(fn, attr)
        tmp_no_whites = [' '.join(x.split()) for x in tmp if x is not None]
        self.data += ', '.join(tmp_no_whites)
        self.data += ']'

    def add_features(self, node):
        features = node.features.copy()
        for f in NON_COMPARABLE_FEATURES:
            features.discard(f)
        if features:
            self.data += ', features=' + str(features)

    def msg_spec(self, node):
        if self.do_indent: self.data += self.indent
        self.data += '{0}'.format(repr(node))

    def element(self, _):
        if self.do_indent: self.data += self.indent
        self.data += 'Element()'

    def string(self, node):
        if self.do_indent: self.data += self.indent
        self.data += 'String({0}'.format(repr(node.value))
        self.add_features(node)
        self.data += ')'

    def word(self, node):
        if self.do_indent: self.data += self.indent
        self.data += 'Word({0}, {1}'.format(repr(node.word), repr(node.pos))
        self.add_features(node)
        self.data += ')'

    def var(self, node):
        if self.do_indent: self.data += self.indent
        if not node.value:
            self.data += 'Var({0}'.format(repr(node.id))
        else:
            self.data += 'Var({0}, {1}'.format(repr(node.id), repr(node.value))
        self.add_features(node)

        self.data += ')'

    def noun_phrase(self, node):
        if self.do_indent: self.data += self.indent
        self.data += 'NounPhrase('
        self.indent += ' ' * len('NounPhrase(')
        self.do_indent = False
        node.head.accept(self)
        if node.specifier != Element():
            self.data += ', '
            node.specifier.accept(self)
        self.add_features(node)
        self.do_indent = True
        self._process_elements(node, 'premodifiers')
        self._process_elements(node, 'complements')
        self._process_elements(node, 'postmodifiers')
        self.data += ')'
        self.indent = self.indent[:-len('NounPhrase(')]

    def phrase(self, node, name='Phrase'):
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
        features = node.features.copy()
        for f in NON_COMPARABLE_FEATURES:
            features.discard(f)
        if features:
            self.data += ',\n'
            self.data += self.indent + 'features=' + str(node.features)
        self._process_elements(node, 'premodifiers')
        self._process_elements(node, 'postmodifiers')
        self.data += ')'
        self.indent = self.indent[:-len(name + '(')]

    def verb_phrase(self, node):
        self.phrase(node, 'VerbPhrase')

    def preposition_phrase(self, node):
        self.phrase(node, 'PrepositionPhrase')

    def adjective_phrase(self, node):
        self.phrase(node, 'AdjectivePhrase')

    def advp(self, node):
        self.phrase(node, 'AdverbPhrase')

    def clause(self, node):
        if self.do_indent: self.data += self.indent
        self.data += 'Clause('
        self.do_indent = False
        node.subject.accept(self)
        self.do_indent = True
        self.data += ',\n'
        self.indent += ' ' * len('Clause(')
        node.predicate.accept(self)
        if node.features:
            self.data += ',\n'
            self.data += self.indent + 'features=' + str(node.features)
        self._process_elements(node, 'front_modifiers')
        self._process_elements(node, 'premodifiers')
        self._process_elements(node, 'complements')
        self._process_elements(node, 'postmodifiers')
        self.data += ')'
        self.indent = self.indent[:-len('Clause(')]

    def coordination(self, node):
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
        if node.features:
            self.data += ',\n' + self.indent
            self.data += 'features=' + str(node.features)
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

    def __init__(self, data='', depth=0, indent='', sep=',\n'):
        super(StrVisitor, self).__init__(depth, indent, sep)
        self.data = data
        self.do_indent = True

    def msg_spec(self, node):
        if self.do_indent: self.data += self.indent
        self.data += '{0}'.format(node)

    def element(self, _):
        self.data += ''

    def string(self, node):
        if self.do_indent: self.data += self.indent
        self.data += 'String({0})'.format(repr(node.value))

    def word(self, node):
        if self.do_indent: self.data += self.indent
        self.data += 'Word({0}, {1})'.format(repr(node.word), repr(node.pos))

    def var(self, node):
        if self.do_indent: self.data += self.indent
        if node.value == Element():
            self.data += 'Var({0})'.format(repr(node.id))
        else:
            self.data += 'Var({0}, {1})'.format(repr(node.id), repr(node.value))

    def noun_phrase(self, node):
        if self.do_indent: self.data += self.indent
        self.data += 'NounPhrase('
        self.indent += ' ' * len('NounPhrase(')
        self.do_indent = False
        node.head.accept(self)
        if node.specifier != Element():
            self.data += ', '
            node.specifier.accept(self)
        self.data += ')'
        self.do_indent = True
        self.indent = self.indent[:-len('NounPhrase(')]

    def phrase(self, node, name=''):
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

    def verb_phrase(self, node):
        self.phrase(node, 'VerbPhrase')

    def preposition_phrase(self, node):
        self.phrase(node, 'PrepositionPhrase')

    def adjective_phrase(self, node):
        self.phrase(node, 'AdjectivePhrase')

    def advp(self, node):
        self.phrase(node, 'AdverbPhrase')

    def clause(self, node):
        self.data += self.indent
        self.data += 'Clause('
        self.do_indent = False
        node.subject.accept(self)
        self.do_indent = True
        self.data += ',\n'
        self.indent += ' ' * len('Clause(')
        node.predicate.accept(self)
        self.data += ')'
        self.indent = self.indent[:-len('Clause(')]

    def coordination(self, node):
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


class SimpleStrVisitor(PrintVisitor):
    """Collect strings of an element and its sub-elements."""

    def __init__(self, data='', depth=0, indent='', sep=',\n'):
        super(SimpleStrVisitor, self).__init__(depth, indent, sep)
        self.data = data
        self.do_indent = True

    def msg_spec(self, node):
        if self.do_indent: self.data += self.indent
        self.data = ' '.join((self.data, node))

    def element(self, _):
        pass

    def string(self, node):
        if self.do_indent: self.data += self.indent
        self.data = ' '.join((self.data, str(node.value)))

    def word(self, node):
        if self.do_indent: self.data += self.indent
        self.data = ' '.join((self.data, str(node.word)))

    def var(self, node):
        if self.do_indent: self.data += self.indent
        if node.value == Element():
            self.data = ' '.join((self.data, str(node.id)))
        else:
            self.data = ' '.join((self.data, str(node.value)))

    def noun_phrase(self, node):
        if node.specifier != Element():
            node.specifier.accept(self)
        for mod in node.premodifiers:
            mod.accept(self)
        node.head.accept(self)
        for mod in node.complements:
            mod.accept(self)
        for mod in node.postmodifiers:
            mod.accept(self)

    def phrase(self, node, _=''):
        for mod in node.premodifiers:
            mod.accept(self)
        node.head.accept(self)
        for mod in node.complements:
            mod.accept(self)
        for mod in node.postmodifiers:
            mod.accept(self)

    def verb_phrase(self, node):
        self.phrase(node, 'VerbPhrase')

    def preposition_phrase(self, node):
        self.phrase(node, 'PrepositionPhrase')

    def adjective_phrase(self, node):
        self.phrase(node, 'AdjectivePhrase')

    def advp(self, node):
        self.phrase(node, 'AdverbPhrase')

    def clause(self, node):
        for mod in node.front_modifiers:
            mod.accept(self)
        if node.subject:
            node.subject.accept(self)
        for mod in node.premodifiers:
            mod.accept(self)
        if node.predicate:
            node.predicate.accept(self)
        for mod in node.complements:
            mod.accept(self)
        for mod in node.postmodifiers:
            mod.accept(self)

    def coordination(self, node):
        i = len(node.coords) - 2
        node.coords[0].accept(self)
        for c in node.coords[1:]:
            i -= 1
            if i > 0:
                self.data += ', '
            else:
                self.data += ' ' + str(node.conj)
            c.accept(self)

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

    def element(self):
        pass

    def string(self, node):
        self.elements.append(node)

    def word(self, node):
        self.elements.append(node)

    def var(self, node):
        self.elements.append(node)

    def noun_phrase(self, node):
        self._process_element(node, 'specifier')
        self._process_elements(node, 'premodifiers')
        self._process_element(node, 'head')
        self._process_elements(node, 'complements')
        self._process_elements(node, 'postmodifiers')

    def phrase(self, node):
        self._process_elements(node, 'premodifiers')
        self._process_element(node, 'head')
        self._process_elements(node, 'complements')
        self._process_elements(node, 'postmodifiers')

    def verb_phrase(self, node):
        self.phrase(node)

    def preposition_phrase(self, node):
        self.phrase(node)

    def adjective_phrase(self, node):
        self.phrase(node)

    def adverb_phrase(self, node):
        self.phrase(node)

    def coordination(self, node):
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

    def element(self):
        pass

    def string(self, node):
        self.elements.append(node)

    def word(self, node):
        self.elements.append(node)

    def var(self, node):
        self.elements.append(node)

    def noun_phrase(self, node):
        self.elements.append(self)
        self._process_element(node, 'specifier')
        self._process_elements(node, 'premodifiers')
        self._process_element(node, 'head')
        self._process_elements(node, 'complements')
        self._process_elements(node, 'postmodifiers')

    def phrase(self, node):
        self.elements.append(self)
        self._process_elements(node, 'premodifiers')
        self._process_element(node, 'head')
        self._process_elements(node, 'complements')
        self._process_elements(node, 'postmodifiers')

    def verb_phrase(self, node):
        self.phrase(node)

    def preposition_phrase(self, node):
        self.phrase(node)

    def adjective_phrase(self, node):
        self.phrase(node)

    def advp(self, node):
        self.phrase(node)

    def coordination(self, node):
        self.elements.append(self)
        self._process_elements(node, 'coords')


def sentence_iterator(sent):
    if isinstance(sent, Clause):
        for x in sentence_iterator(sent.predicate):
            yield x
        yield sent.predicate
        yield sent.subject
        return

    if isinstance(sent, Phrase):
        for o in reversed(sent.postmodifiers):
            for x in sentence_iterator(o):
                yield x

        for o in reversed(sent.complements):
            for x in sentence_iterator(o):
                yield x

        if sent.head is not None:
            for x in sentence_iterator(sent.head):
                yield x

        for o in reversed(sent.premodifiers):
            for x in sentence_iterator(o):
                yield x

        if isinstance(sent, NounPhrase):
            for x in sentence_iterator(sent.specifier):
                yield x

    if isinstance(sent, Coordination):
        for x in sent.coords:
            yield x
        yield sent
    else:
        yield (sent)


def aggregation_sentence_iterator(sent):
    if isinstance(sent, Clause):
        for x in sentence_iterator(sent.predicate):
            yield x
        return

    if isinstance(sent, Phrase):
        for o in reversed(sent.postmodifiers):
            for x in sentence_iterator(o):
                yield x

    for o in reversed(sent.complements):
        for x in sentence_iterator(o):
            yield x

    for o in reversed(sent.premodifiers):
        for x in sentence_iterator(o):
            yield x

    else:
        yield (sent)


def replace_element(sent, elt, replacement=None):
    import warnings
    warnings.warn('replace_element is deprecated')
    if sent == elt:
        return True

    if isinstance(sent, Clause):
        if sent.subject == elt:
            sent.subject = replacement
            return True
        else:
            if replace_element(sent.subject, elt, replacement):
                return True

        if sent.predicate == elt:
            sent.predicate = replacement
            return True

        else:
            if replace_element(sent.predicate, elt, replacement):
                return True

    if isinstance(sent, Coordination):
        for i, o in list(enumerate(sent.coords)):
            if o == elt:
                if replacement is None:
                    del sent.coords[i]
                else:
                    sent.coords[i] = replacement
                return True
            else:
                if replace_element(o, elt, replacement):
                    return True

    if isinstance(sent, Phrase):
        for i, o in reversed(list(enumerate(sent.postmodifiers))):
            if o == elt:
                if replacement is None:
                    del sent.postmodifiers[i]
                else:
                    sent.postmodifiers[i] = replacement
                return True
            else:
                if replace_element(o, elt, replacement):
                    return True
        for i, o in reversed(list(enumerate(sent.complements))):
            if o == elt:
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
        for i, o in reversed(list(enumerate(sent.premodifiers))):
            if o == elt:
                if replacement is None:
                    del sent.premodifiers[i]
                else:
                    sent.premodifiers[i] = replacement
                return True
            else:
                if replace_element(o, elt, replacement):
                    return True

        if isinstance(sent, NounPhrase):
            if sent.specifier == elt:
                sent.specifier = replacement
                return True

    return False


def replace_element_with_id(sent, elt_id, replacement=None):
    import warnings
    warnings.warn('replace_element is deprecated')

    if id(sent) == elt_id:
        return True

    if isinstance(sent, Coordination):
        for i, o in list(enumerate(sent.coords)):
            if id(o) == elt_id:
                if replacement is None:
                    del sent.coords[i]
                else:
                    sent.coords[i] = replacement
                return True
            else:
                if replace_element_with_id(o, elt_id, replacement):
                    return True

    if isinstance(sent, Clause):
        for i, o in reversed(list(enumerate(sent.premodifiers))):
            if id(o) == elt_id:
                if replacement is None:
                    del sent.premodifiers[i]
                else:
                    sent.premodifiers[i] = replacement
                return True
            else:
                if replace_element_with_id(o, elt_id, replacement):
                    return True

        if id(sent.subject) == elt_id:
            sent.subject = replacement or Element()
            return True
        else:
            if replace_element_with_id(sent.subject, elt_id, replacement):
                return True

        if id(sent.predicate) == elt_id:
            sent.predicate = replacement
            return True

        else:
            if replace_element_with_id(sent.predicate, elt_id, replacement):
                return True

        for i, o in reversed(list(enumerate(sent.complements))):
            if id(o) == elt_id:
                if replacement is None:
                    del sent.complements[i]
                else:
                    sent.complements[i] = replacement
                return True
            else:
                if replace_element_with_id(o, elt_id, replacement):
                    return True

        for i, o in reversed(list(enumerate(sent.postmodifiers))):
            if id(o) == elt_id:
                if replacement is None:
                    del sent.postmodifiers[i]
                else:
                    sent.postmodifiers[i] = replacement
                return True
            else:
                if replace_element_with_id(o, elt_id, replacement):
                    return True

    if isinstance(sent, Phrase):
        for i, o in reversed(list(enumerate(sent.postmodifiers))):
            if id(o) == elt_id:
                if replacement is None:
                    del sent.postmodifiers[i]
                else:
                    sent.postmodifiers[i] = replacement
                return True
            else:
                if replace_element_with_id(o, elt_id, replacement):
                    return True
        for i, o in reversed(list(enumerate(sent.complements))):
            if id(o) == elt_id:
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
        for i, o in reversed(list(enumerate(sent.premodifiers))):
            if id(o) == elt_id:
                if replacement is None:
                    del sent.premodifiers[i]
                else:
                    sent.premodifiers[i] = replacement
                return True
            else:
                if replace_element_with_id(o, elt_id, replacement):
                    return True

        if isinstance(sent, NounPhrase):
            if sent.specifier == elt_id:
                sent.specifier = replacement
                return True
    return False

# Penn Treebank Tags


# Number Tag    Description
# 1.     Coordination      Coordinating conjunction
# 2.     CD      Cardinal number
# 3.     DT      Determiner
# 4.     EX      Existential there
# 5.     FW      Foreign word
# 6.     IN      Preposition or subordinating conjunction
# 7.     JJ      Adjective
# 8.     JJR     Adjective, comparative
# 9.     JJS     Adjective, superlative
# 10.	LS      List item marker
# 11.	MD      Modal
# 12.	NN      Noun, singular or mass
# 13.	NNS     Noun, plural
# 14.	NNP     Proper noun, singular
# 15.	NNPS	Proper noun, plural
# 16.	PDT     Predeterminer
# 17.	POS     Possessive ending
# 18.	PRP     Personal pronoun
# 19.	PRP$	Possessive pronoun
# 20.	RB      Adverb
# 21.	RBR     Adverb, comparative
# 22.	RBS     Adverb, superlative
# 23.	RP      Particle
# 24.	SYM     Symbol
# 25.	TO      to
# 26.	UH      Interjection
# 27.	VB      Verb, base form
# 28.	VBD     Verb, past tense
# 29.	VBG     Verb, gerund or present participle
# 30.	VBN     Verb, past participle
# 31.	VBP     Verb, non-3rd person singular present
# 32.	VBZ     Verb, 3rd person singular present
# 33.	WDT     Wh-determiner
# 34.	WP      Wh-pronoun
# 35.	WP$	    Possessive wh-pronoun
# 36.	WRB     Wh-adverb
