import logging

from nlglib.macroplanning import Document, Paragraph
from nlglib.microplanning import is_clause_type
from nlglib.features import category, NUMBER, GENDER, CASE, TENSE, NEGATED, MODAL, FeatureGroup
from nlglib.utils import flatten


# a complementiser group
complementiser = FeatureGroup('complementiser')


class Realiser(object):

    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)

    def __call__(self, msg, **kwargs):
        return self.realise(msg, **kwargs)

    def realise(self, msg, **kwargs):
        if msg is None:
            return ''
        elif msg.category in category.element_category:
            return self.element(msg, **kwargs)
        elif isinstance(msg, (list, set, tuple)) or msg.category == category.ELEMENT_LIST:
            return self.element_list(msg, **kwargs)
        elif msg.category == category.MSG:
            return self.message_specification(msg, **kwargs)
        elif msg.category == category.RST:
            return self.rst_relation(msg, **kwargs)
        elif msg.category == category.DOCUMENT:
            return self.document(msg, **kwargs)
        elif msg.category == category.PARAGRAPH:
            return self.paragraph(msg, **kwargs)
        else:
            return msg.realise(self, **kwargs) if hasattr(msg, 'realise') else str(msg)

    # noinspection PyUnusedLocal
    def element(self, elt, **kwargs):
        """ Realise NLG element. """
        self.logger.debug('Realising element (simple realisation):\n{0}'.format(repr(elt)))
        v = RealisationVisitor()
        elt.accept(v)
        result = str(v).replace(' ,', ',')
        if result:
            return '{0}{1}.'.format(result[:1].upper(), result[1:])
        else:
            return ''

    # noinspection PyUnusedLocal
    def message_specification(self, msg, **kwargs):
        """ Realise message specification - this should not happen """
        self.logger.error('Realising message spec:\n{0}'.format(repr(msg)))
        return str(msg).strip()

    def element_list(self, elt, **kwargs):
        """ Realise a list. """
        self.logger.debug('Realising list of elements:\n{0}'.format(repr(elt)))
        return ' '.join(self.realise(x, **kwargs) for x in elt)

    def rst_relation(self, msg, **kwargs):
        """ Return a copy of Message with strings. """
        self.logger.debug('Realising message:\n{0}'.format(repr(msg)))
        if msg is None: return None
        nuclei = [self.realise(n, **kwargs) for n in msg.nuclei]
        satellite = self.realise(msg.satellite, **kwargs)
        sentences = flatten(nuclei + [satellite])
        self.logger.debug('flattened sentences: %s' % sentences)
        return ' '.join(sentences).strip()

    def document(self, msg, **kwargs):
        """ Return a copy of a Document with strings. """
        self.logger.debug('Realising document.')
        if msg is None:
            return None
        title = self.realise(msg.title, **kwargs)
        if not kwargs.get('keep_title_punctuation') and title.endswith('.'):
            title = title[:-1]
        sections = [self.realise(x, **kwargs) for x in msg.sections]
        return Document(title, *sections)

    def paragraph(self, msg, **kwargs):
        """ Return a copy of a Paragraph with strings. """
        self.logger.debug('Realising paragraph.')
        if msg is None:
            return None
        sentences = [self.realise(x, **kwargs) for x in msg.sentences]
        return Paragraph(*sentences)


# **************************************************************************** #


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

    def element(self, node):
        pass

    def string(self, node):
        if NEGATED.true in node:
            self.text += 'not '
        self.text += node.value + ' '

    def word(self, node):
        word = node.word
        # if (node.has_feature('NUMBER', 'PLURAL') and node.pos == 'NOUN'):
        #     word = lexicon.pluralise_noun(node.word)
        if NEGATED.true in node:
            self.text += 'not '
        self.text += word + ' '

    def var(self, node):
        if node.value:
            node.value.accept(self)
        else:
            self.text += str(node.id)
        self.text += ' '

    def clause(self, node):
        # do a bit of coordination
        node.predicate.features.update(node.features)
        node.predicate.features.replace(node.subject[NUMBER])
        node.predicate.features.replace(node.subject[GENDER])
        node.predicate.features.replace(node.subject[CASE])
        node.predicate.features.replace(node[NEGATED])
        for o in node.front_modifiers: o.accept(self)
        node.subject.accept(self)
        for o in node.premodifiers: o.accept(self)
        node.predicate.accept(self)
        if len(node.complements) > 0:
            if complementiser in node.complements[0]:
                self.text += node.complements[0][complementiser]
                self.text += ' '
        for c in node.complements: c.accept(self)
        for o in node.postmodifiers: o.accept(self)

    def coordination(self, node):
        if node.coords is None or len(node.coords) == 0: return ''
        if len(node.coords) == 1:
            node.coords[0].accept(self)
            return
        for i, x in enumerate(node.coords):
            x.accept(self)
            conjunction = str(node.conj)
            if conjunction == 'and' and i < len(node.coords) - 2:
                self.text += ', '
            elif i < len(node.coords) - 1:
                conj = conjunction
                if is_clause_type(self): conj = ', ' + conjunction
                self.text += ' ' + conj + ' '

    def noun_phrase(self, node):
        node.specifier.accept(self)
        for c in node.premodifiers: c.accept(self)
        node.head.accept(self)
        if len(node.complements) > 0:
            if complementiser in node.complements[0]:
                self.text += node.complements[0][complementiser]
                self.text += ' '
        for c in node.complements: c.accept(self)
        for c in node.postmodifiers: c.accept(self)

    def verb_phrase(self, node):
        for c in node.premodifiers: c.accept(self)
        tmp_vis = RealisationVisitor()
        node.head.accept(tmp_vis)
        head = str(tmp_vis)
        if MODAL in node:
            self.text += ' ' + node[MODAL] + ' '
            if NEGATED.true in node:
                self.text += 'not '
            node.head.accept(self)
        # hs the head a modal verb?
        elif head in MODAL:
            self.text += ' '
            node.head.accept(self)
            self.text += ' '
            if NEGATED.true in node:
                self.text += 'not '
        elif head == 'have':
            if NEGATED.true in node:
                self.text += 'do not have '
            else:
                self.text += 'have '
        elif head == 'has':
            if NEGATED.true in node:
                self.text += 'does not have '
            else:
                self.text += 'has '
        elif head == 'be' or head == 'is':
            if NUMBER.plural in node:
                if TENSE.past in node:
                    self.text += 'were '
                else:
                    self.text += 'are '
            else:
                if TENSE.past in node:
                    self.text += 'was '
                else:
                    self.text += 'is '
            if NEGATED.true in node:
                self.text += 'not '
        else:
            if NEGATED.true in node:
                self.text += 'does not '
            node.head.accept(self)
        if len(node.complements) > 0:
            if complementiser in node.complements[0]:
                self.text += ' ' + node.complements[0][complementiser] + ' '
        for c in node.complements:
            c.accept(self)
        for c in node.postmodifiers: c.accept(self)

    def preposition_phrase(self, node):
        self.phrase(node)

    def adjective_phrase(self, node):
        self.phrase(node)

    def adverb_phrase(self, node):
        self.phrase(node)

    def phrase(self, node):
        for c in node.premodifiers: c.accept(self)
        node.head.accept(self)
        if complementiser in node:
            self.text += ' {0} '.format(node[complementiser])
        for c in node.complements: c.accept(self)
        for c in node.postmodifiers: c.accept(self)
