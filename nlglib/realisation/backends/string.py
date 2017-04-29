from nlglib import logger

from nlglib.structures import (Element, MsgSpec, Message,
                               Paragraph, Section, Document, is_clause_t)
from nlglib import lexicon


def realise(msg, **kwargs):
    """ Perform lexicalisation on the message depending on the type. """
    simple = kwargs.get('simple', True)
    if msg is None:
        return None
    elif isinstance(msg, str):
        return msg
    elif isinstance(msg, Element):
        return realise_element(msg, **kwargs)
    elif isinstance(msg, MsgSpec):
        return realise_message_spec(msg, **kwargs)
    elif isinstance(msg, (list, tuple)):
        return realise_list(msg, **kwargs)
    elif isinstance(msg, Message):
        return realise_message(msg, **kwargs)
    elif isinstance(msg, Paragraph):
        return realise_paragraph(msg, **kwargs)
    elif isinstance(msg, Section):
        return realise_section(msg, **kwargs)
    elif isinstance(msg, Document):
        return realise_document(msg, **kwargs)
    else:
        raise TypeError('"%s" is neither a Message nor a MsgInstance' %
                        type(msg))


def realise_element(elt, **kwargs):
    """ Realise NLG element. """
    logger.debug('Realising element (simple realisation):\n{0}'
                 .format(repr(elt)))
    return simple_realisation(elt, **kwargs)


def realise_message_spec(msg, **kwargs):
    """ Realise message specification - this should not happen """
    logger.debug('Realising message spec:\n{0}'.format(repr(msg)))
    return str(msg).strip()


def realise_list(elt, **kwargs):
    """ Realise a list. """
    logger.debug('Realising list of elements:\n{0}'.format(repr(elt)))
    return ' '.join(realise(x, **kwargs) for x in elt)


def realise_message(msg, **kwargs):
    """ Return a copy of Message with strings. """
    logger.debug('Realising message:\n{0}'.format(repr(msg)))
    if msg is None: return None
    nucl = realise(msg.nucleus, **kwargs)
    sats = [realise(x, **kwargs) for x in msg.satellites if x is not None]
    #    if len(sats) > 0:
    #        sats[0].add_front_modifier(Word(msg.marker, 'ADV'))
    sentences = _flatten([nucl] + sats)
    logger.debug('flattened sentences: %s' % sentences)
    # TODO: this si wrong because the recursive call can apply capitalisation
    # and punctuation multiple times...
    sentences = list(map(lambda e: e[:1].upper() + e[1:] +
                                   ('.' if e[-1] != '.' else ''),
                         [s for s in sentences if s != '']))
    return sentences


def realise_paragraph(msg, **kwargs):
    """ Return a copy of Paragraph with strings. """
    logger.debug('Realising paragraph.')
    if msg is None:
        return None
    messages = [realise(x, **kwargs) for x in msg.messages]
    messages = _flatten(messages)
    return Paragraph(*messages)


def realise_section(msg, **kwargs):
    """ Return a copy of a Section with strings. """
    logger.debug('Realising section.')
    if msg is None:
        return None
    title = realise(msg.title, **kwargs)
    paragraphs = [Paragraph(realise(x, **kwargs)) for x in msg.content]
    return Section(title, *paragraphs)


def realise_document(msg, **kwargs):
    """ Return a copy of a Document with strings. """
    logger.debug('Realising document.')
    if msg is None:
        return None
    title = realise(msg.title, **kwargs)
    sections = [realise(x, **kwargs) for x in msg.sections]
    return Document(title, *sections)


def _flatten(lst):
    """ Return a list where all elemts are items. 
    Any encountered list will be expanded.

    """
    result = list()
    for x in lst:
        if isinstance(x, list):
            for y in x:
                result.append(y)
        else:
            if x is not None:
                result.append(x)
    return result


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
        if (node.has_feature('NUMBER', 'PLURAL') and
                    node.pos == 'NOUN'):
            word = lexicon.pluralise_noun(node.word)
        if node.has_feature('NEGATED', 'true'):
            self.text += 'not '
        self.text += word + ' '

    def visit_var(self, node):
        if node.value:
            node.value.accept(self)
        else:
            self.text += str(self.id)
        self.text += ' '

    def visit_clause(self, node):
        # do a bit of coordination
        logger.debug('Clause is "{0}"'.format(repr(node)))
        node.vp.add_features(node._features)
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
        for o in node.pre_modifiers: o.accept(self)
        node.vp.accept(self)
        if len(node.complements) > 0:
            if node.complements[0].has_feature('COMPLEMENTISER'):
                self.text += node.complements[0].get_feature('COMPLEMENTISER')
                self.text += ' '
        for c in node.complements: c.accept(self)
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

    def visit_np(self, node):
        for c in node.front_modifiers: c.accept(self)
        node.spec.accept(self)
        for c in node.pre_modifiers: c.accept(self)
        node.head.accept(self)
        if len(node.complements) > 0:
            if node.complements[0].has_feature('COMPLEMENTISER'):
                self.text += node.complements[0].get_feature('COMPLEMENTISER')
                self.text += ' '
        for c in node.complements: c.accept(self)
        for c in node.post_modifiers: c.accept(self)

    def visit_vp(self, node):
        for c in node.front_modifiers: c.accept(self)
        for c in node.pre_modifiers: c.accept(self)
        tmp_vis = RealisationVisitor()
        node.head.accept(tmp_vis)
        head = str(tmp_vis)
        logger.debug('VP is "{0}"'.format(repr(node)))
        logger.debug('  head of VP is "{0}"'.format(head))
        modals = [f for f in lexicon.Modal.values]
        # logger.warning('Modals: {}'.format(modals))
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
        if node.has_feature('COMPLEMENTISER'):
            self.text += ' {0} '.format(node.get_feature('COMPLEMENTISER'))
        for c in node.complements: c.accept(self)
        for c in node.post_modifiers: c.accept(self)


def simple_realisation(struct, **kwargs):
    """ Use the RealisationVisitor that performs only the most basic realisation
    and return the created surface realisation as a string.

    """
    v = RealisationVisitor()
    struct.accept(v)
    result = str(v).replace(' ,', ',')
    if result:
        return '{0}{1}.'.format(result[:1].upper(), result[1:])
    else:
        return ''
