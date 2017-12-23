import logging
import string

from nlglib.structures import Document, is_clause_t
from nlglib.features import category
from nlglib.utils import flatten


class Realiser(object):

    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)

    def __call__(self, msg, **kwargs):
        return self.realise(msg, **kwargs)

    def realise(self, msg, **kwargs):
        if msg is None:
            return ''
        elif msg.category in category.ELEMENT_CATEGORIES:
            return self.realise_element(msg, **kwargs)
        elif msg.category == category.MSG:
            return self.realise_message_spec(msg, **kwargs)
        elif msg.category == category.ELEMENT_LIST:
            return self.realise_list(msg, **kwargs)
        elif msg.category == category.RST:
            return self.realise_message(msg, **kwargs)
        elif msg.category == category.DOCUMENT:
            return self.realise_document(msg, **kwargs)
        else:
            return str(msg)

    def realise_element(self, elt, **kwargs):
        """ Realise NLG element. """
        self.logger.debug('Realising element (simple realisation):\n{0}'.format(repr(elt)))
        v = RealisationVisitor()
        elt.accept(v)
        result = str(v).replace(' ,', ',')
        if result:
            return '{0}{1}.'.format(result[:1].upper(), result[1:])
        else:
            return ''

    def realise_message_spec(self, msg, **kwargs):
        """ Realise message specification - this should not happen """
        self.logger.debug('Realising message spec:\n{0}'.format(repr(msg)))
        return str(msg).strip()

    def realise_list(self, elt, **kwargs):
        """ Realise a list. """
        self.logger.debug('Realising list of elements:\n{0}'.format(repr(elt)))
        return ' '.join(self.realise(x, **kwargs) for x in elt)

    def realise_message(self, msg, **kwargs):
        """ Return a copy of Message with strings. """
        self.logger.debug('Realising message:\n{0}'.format(repr(msg)))
        if msg is None: return None
        nuclei = [self.realise(n, **kwargs) for n in msg.nuclei]
        satellite = self.realise(msg.satellite, **kwargs)
        sentences = flatten(nuclei + [satellite])
        self.logger.debug('flattened sentences: %s' % sentences)
        rv = []
        for s in sentences:
            if not s:
                continue
            formatted_sent = s[0].upper() + s[1:]
            if formatted_sent[-1] not in string.punctuation:
                formatted_sent += '.'
            rv.append(formatted_sent)
        return sentences

    def realise_document(self, msg, **kwargs):
        """ Return a copy of a Document with strings. """
        self.logger.debug('Realising document.')
        if msg is None:
            return None
        title = self.realise(msg.title, **kwargs)
        sections = [self.realise(x, **kwargs) for x in msg.sections]
        return Document(title, *sections)


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

    def visit_element(self, node):
        pass

    def visit_string(self, node):
        if node.has_feature('NEGATED', 'true'):
            self.text += 'not '
        self.text += node.value + ' '

    def visit_word(self, node):
        word = node.word
        # if (node.has_feature('NUMBER', 'PLURAL') and node.pos == 'NOUN'):
        #     word = lexicon.pluralise_noun(node.word)
        if node.has_feature('NEGATED', 'true'):
            self.text += 'not '
        self.text += word + ' '

    def visit_var(self, node):
        if node.value:
            node.value.accept(self)
        else:
            self.text += str(node.id)
        self.text += ' '

    def visit_clause(self, node):
        # do a bit of coordination
        node.vp.features.update(node.features)
        if node.subj.has_feature('NUMBER'):
            node.vp.set_feature('NUMBER', node.subj.get_feature('NUMBER'))
        if node.subj.has_feature('GENDER'):
            node.vp.set_feature('GENDER', node.subj.get_feature('GENDER'))
        if node.subj.has_feature('CASE'):
            node.vp.set_feature('CASE', node.subj.get_feature('CASE'))
        if node.has_feature('NEGATED'):
            node.vp.set_feature('NEGATED', node.get_feature('NEGATED'))
        for o in node.front_modifiers: o.accept(self)
        node.subj.accept(self)
        for o in node.premodifiers: o.accept(self)
        node.vp.accept(self)
        if len(node.complements) > 0:
            if node.complements[0].has_feature('COMPLEMENTISER'):
                self.text += node.complements[0].get_feature('COMPLEMENTISER')
                self.text += ' '
        for c in node.complements: c.accept(self)
        for o in node.postmodifiers: o.accept(self)

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

    def visit_noun_phrase(self, node):
        node.spec.accept(self)
        for c in node.premodifiers: c.accept(self)
        node.head.accept(self)
        if len(node.complements) > 0:
            if node.complements[0].has_feature('COMPLEMENTISER'):
                self.text += node.complements[0].get_feature('COMPLEMENTISER')
                self.text += ' '
        for c in node.complements: c.accept(self)
        for c in node.postmodifiers: c.accept(self)

    def visit_verb_phrase(self, node):
        for c in node.premodifiers: c.accept(self)
        tmp_vis = RealisationVisitor()
        node.head.accept(tmp_vis)
        head = str(tmp_vis)
        modals = [
            'can', 'could',
            'may', 'might',
            'must', 'ought',
            'shall', 'should',
            'will', 'would'
        ]
        if node.has_feature('MODAL'):
            self.text += ' ' + node.get_feature('MODAL') + ' '
            if node.has_feature('NEGATED', 'true'):
                self.text += 'not '
            node.head.accept(self)
        # hs the head a modal verb?
        elif head in modals:
            self.text += ' '
            node.head.accept(self)
            self.text += ' '
            if node.has_feature('NEGATED', 'true'):
                self.text += 'not '
        elif head == 'have':
            if node.has_feature('NEGATED', 'true'):
                self.text += 'do not have '
            else:
                self.text += 'have '
        elif head == 'has':
            if node.has_feature('NEGATED', 'true'):
                self.text += 'does not have '
            else:
                self.text += 'has '
        elif head == 'be' or head == 'is':
            if node.has_feature('NUMBER', 'PLURAL'):
                if node.has_feature('TENSE', 'PAST'):
                    self.text += 'were '
                else:
                    self.text += 'are '
            else:
                if node.has_feature('TENSE', 'PAST'):
                    self.text += 'was '
                else:
                    self.text += 'is '
            if node.has_feature('NEGATED', 'true'):
                self.text += 'not '
        else:
            if node.has_feature('NEGATED', 'true'):
                self.text += 'does not '
            node.head.accept(self)
        if len(node.complements) > 0:
            if node.complements[0].has_feature('COMPLEMENTISER'):
                self.text += ' {0} '.format(
                    node.complements[0].get_feature('COMPLEMENTISER'))
        for c in node.complements:
            c.accept(self)
        for c in node.postmodifiers: c.accept(self)

    def visit_preposition_phrase(self, node):
        self.visit_phrase(node)

    def visit_adjective_phrase(self, node):
        self.visit_phrase(node)

    def visit_advp(self, node):
        self.visit_phrase(node)

    def visit_phrase(self, node):
        for c in node.front_modifiers: c.accept(self)
        for c in node.premodifiers: c.accept(self)
        node.head.accept(self)
        if node.has_feature('COMPLEMENTISER'):
            self.text += ' {0} '.format(node.get_feature('COMPLEMENTISER'))
        for c in node.complements: c.accept(self)
        for c in node.postmodifiers: c.accept(self)
