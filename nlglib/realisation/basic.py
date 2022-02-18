import logging

from nlglib.macroplanning import Document, Paragraph
from nlglib.microplanning import is_clause_type
from nlglib.features import category, Number, Gender, Case, Tense, Negated, Modal, FeatureGroup
from nlglib.utils import flatten

__all__ = ['Realiser']

# a complementiser group
complementiser = FeatureGroup('complementiser')


class Realiser(object):

    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)

    def __call__(self, msg, **kwargs):
        return self.realise(msg, **kwargs)

    def realise(self, msg, **kwargs):
        """Perform surface realisation of the given `msg` (convert to text)

        If the object has an attribute 'realise', it will be called with args (self, **kwargs).
        Otherwise, get the object's category (`msg.category`) or type name
        and try to look up the attribute with the same name in `self` (dynamic dispatch).
        List, set and tuple are realised by `element_list()`. Lastly,
        if no method matches, return `str(msg)`.

        """
        cat = msg.category if hasattr(msg, 'category') else type(msg).__name__
        self.logger.debug('Realising {0}: {1}'.format(cat, repr(msg)))

        if msg is None:
            return ''

        if hasattr(msg, 'realise'):
            return msg.realise(self, **kwargs)

        # support dynamic dispatching
        attribute = cat.lower()
        if hasattr(self, attribute):
            fn = getattr(self, attribute)
            return fn(msg, **kwargs)
        elif cat in category.ElementCategory:
            return self.element(msg, **kwargs)
        elif isinstance(msg, (list, set, tuple)):
            return self.element_list(msg, **kwargs)
        else:
            return str(msg)

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


# TODO: Move to visitors?
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
        if Negated.true in node:
            self.text += 'not '
        self.text += node.value + ' '

    def word(self, node):
        word = node.word
        # if (node.has_feature('Number', 'PLURAL') and node.pos == 'NOUN'):
        #     word = lexicon.pluralise_noun(node.word)
        if Negated.true in node:
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
        node.predicate.features.replace(node.subject[Number])
        node.predicate.features.replace(node.subject[Gender])
        node.predicate.features.replace(node.subject[Case])
        node.predicate.features.replace(node[Negated])
        for o in node.front_modifiers:
            o.accept(self)
        node.subject.accept(self)
        for o in node.premodifiers:
            o.accept(self)
        node.predicate.accept(self)
        if len(node.complements) > 0:
            if complementiser in node.complements[0]:
                self.text += node.complements[0][complementiser]
                self.text += ' '
        for c in node.complements:
            c.accept(self)
        for o in node.postmodifiers:
            o.accept(self)

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
        for c in node.premodifiers:
            c.accept(self)
        node.head.accept(self)
        if len(node.complements) > 0:
            if complementiser in node.complements[0]:
                self.text += node.complements[0][complementiser]
                self.text += ' '
        for c in node.complements:
            c.accept(self)
        for c in node.postmodifiers:
            c.accept(self)

    def verb_phrase(self, node):
        for c in node.premodifiers:
            c.accept(self)
        tmp_vis = RealisationVisitor()
        node.head.accept(tmp_vis)
        head = str(tmp_vis)
        if Modal in node:
            self.text += ' ' + node[Modal] + ' '
            if Negated.true in node:
                self.text += 'not '
            node.head.accept(self)
        # hs the head a modal verb?
        elif head in Modal:
            self.text += ' '
            node.head.accept(self)
            self.text += ' '
            if Negated.true in node:
                self.text += 'not '
        elif head == 'have':
            if Negated.true in node:
                self.text += 'do not have '
            else:
                self.text += 'have '
        elif head == 'has':
            if Negated.true in node:
                self.text += 'does not have '
            else:
                self.text += 'has '
        elif head == 'be' or head == 'is':
            if Number.plural in node:
                if Tense.past in node:
                    self.text += 'were '
                else:
                    self.text += 'are '
            else:
                if Tense.past in node:
                    self.text += 'was '
                else:
                    self.text += 'is '
            if Negated.true in node:
                self.text += 'not '
        else:
            if Negated.true in node:
                self.text += 'does not '
            node.head.accept(self)
        if len(node.complements) > 0:
            if complementiser in node.complements[0]:
                self.text += ' ' + node.complements[0][complementiser] + ' '
        for c in node.complements:
            c.accept(self)
        for c in node.postmodifiers:
            c.accept(self)

    def preposition_phrase(self, node):
        self.phrase(node)

    def adjective_phrase(self, node):
        self.phrase(node)

    def adverb_phrase(self, node):
        self.phrase(node)

    def phrase(self, node):
        for c in node.premodifiers:
            c.accept(self)
        node.head.accept(self)
        if complementiser in node:
            self.text += ' {0} '.format(node[complementiser])
        for c in node.complements:
            c.accept(self)
        for c in node.postmodifiers:
            c.accept(self)
