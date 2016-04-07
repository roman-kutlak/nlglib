import logging
from urllib.parse import unquote_plus

import nlglib
from nlglib.structures import *
from nlglib import lexicon
from nlglib.microplanning import XmlVisitor
from nlglib.simplenlg import SimplenlgClient

""" This package provides functionality for surface realising NLG Elements.

The only supported format at the moment is text although the future versions
should contain support for HTML (and possibly other useful formats such as ODF).

The input is a document where NLG Elements were already realised to strings.

"""


logging.getLogger(__name__).addHandler(logging.NullHandler())

def get_log():
    return logging.getLogger(__name__)


class Realiser:
    def __init__(self, simple=False):
        self.simple = simple

    def __enter__(self):
        pass

    def __exit__(self, type, value, traceback):
        pass

    def realise(self, msg):
        """ Perform lexicalisation on the message depending on the type. """
        if msg is None:                  return None
        elif isinstance(msg, str):       return msg
        elif isinstance(msg, Element):   return self.realise_element(msg)
        elif isinstance(msg, MsgSpec):   return self.realise_message_spec(msg)
        elif isinstance(msg, Message):   return self.realise_message(msg)
        elif isinstance(msg, Paragraph): return self.realise_paragraph(msg)
        elif isinstance(msg, Section):   return self.realise_section(msg)
        elif isinstance(msg, Document):  return self.realise_document(msg)
        else:
            raise TypeError('"%s" is neither a Message nor a MsgInstance' % msg)


    def realise_element(self, elt):
        """ Realise NLG element. """
        if nlglib.nlg.simplenlg_client is not None and not self.simple:
            get_log().debug('Realising element (SimpleNLG realisation):\n{0}'
                            .format(repr(elt)))
            return simpleNlg_realisation(elt)
        else:
            get_log().debug('Realising element (simple realisation):\n{0}'
                            .format(repr(elt)))
            return simple_realisation(elt)


    def realise_message_spec(self, msg):
        """ Realise message specification - this should not happen """
        get_log().debug('Realising message spec:\n{0}'.format(repr(msg)))
        return str(msg).strip()


    def realise_message(self, msg):
        """ Return a copy of Message with strings. """
        get_log().debug('Realising message:\n{0}'.format(repr(msg)))
        if msg is None: return None
        nucl = self.realise(msg.nucleus)
        sats = [self.realise(x) for x in msg.satelites if x is not None]
    #    if len(sats) > 0:
    #        sats[0].add_front_modifier(Word(msg.marker, 'ADV'))
        sentences = _flatten([nucl] + sats)
        get_log().debug('flattened sentences: %s' % sentences)
        # TODO: this si wrong because the recursive call can apply capitalisation
        # and punctuation multiple times...
        sentences = list(map(lambda e: e[:1].upper() + e[1:] + \
                                        ('.' if e[-1] != '.' else ''),
                             [s for s in sentences if s != '']))
        return sentences


    def realise_paragraph(self, msg):
        """ Return a copy of Paragraph with strings. """
        get_log().debug('Realising paragraph.')
        if msg is None: return None
        messages = [self.realise(x) for x in msg.messages]
        messages = _flatten(messages)
        return Paragraph(*messages)


    def realise_section(self, msg):
        """ Return a copy of a Section with strings. """
        get_log().debug('Realising section.')
        if msg is None: return None
        title = self.realise(msg.title)
        paragraphs = [Paragraph(self.realise(x)) for x in msg.paragraphs]
        return Section(title, *paragraphs)


    def realise_document(self, msg):
        """ Return a copy of a Document with strings. """
        get_log().debug('Realising document.')
        if msg is None: return None
        title = self.realise(msg.title)
        sections = [self.realise(x) for x in msg.sections]
        return Document(title, *sections)


def realise(msg):
    """ Perform lexicalisation on the message depending on the type. """
    if msg is None:                  return None
    elif isinstance(msg, str):       return msg
    elif isinstance(msg, Element):   return realise_element(msg)
    elif isinstance(msg, MsgSpec):   return realise_message_spec(msg)
    elif isinstance(msg, Message):   return realise_message(msg)
    elif isinstance(msg, Paragraph): return realise_paragraph(msg)
    elif isinstance(msg, Section):   return realise_section(msg)
    elif isinstance(msg, Document):  return realise_document(msg)
    else:
        raise TypeError('"%s" is neither a Message nor a MsgInstance' % msg)


def realise_element(elt):
    """ Realise NLG element. """
    get_log().debug('Realising element (simple realisation):\n{0}'
                    .format(repr(elt)))
    return simple_realisation(elt)


def realise_message_spec(msg):
    """ Realise message specification - this should not happen """
    get_log().debug('Realising message spec:\n{0}'.format(repr(msg)))
    return str(msg).strip()


def realise_message(msg):
    """ Return a copy of Message with strings. """
    get_log().debug('Realising message:\n{0}'.format(repr(msg)))
    if msg is None: return None
    nucl = realise(msg.nucleus)
    sats = [realise(x) for x in msg.satelites if x is not None]
#    if len(sats) > 0:
#        sats[0].add_front_modifier(Word(msg.marker, 'ADV'))
    sentences = _flatten([nucl] + sats)
    get_log().debug('flattened sentences: %s' % sentences)
    # TODO: this si wrong because the recursive call can apply capitalisation
    # and punctuation multiple times...
    sentences = list(map(lambda e: e[:1].upper() + e[1:] + \
                                    ('.' if e[-1] != '.' else ''),
                         [s for s in sentences if s != '']))
    return sentences


def realise_paragraph(msg):
    """ Return a copy of Paragraph with strings. """
    get_log().debug('Realising paragraph.')
    if msg is None: return None
    messages = [realise(x) for x in msg.messages]
    messages = _flatten(messages)
    return Paragraph(*messages)


def realise_section(msg):
    """ Return a copy of a Section with strings. """
    get_log().debug('Realising section.')
    if msg is None: return None
    title = realise(msg.title)
    paragraphs = [Paragraph(realise(x)) for x in msg.paragraphs]
    return Section(title, *paragraphs)


def realise_document(msg):
    """ Return a copy of a Document with strings. """
    get_log().debug('Realising document.')
    if msg is None: return None
    title = realise(msg.title)
    sections = [realise(x) for x in msg.sections]
    return Document(title, *sections)


def _flatten(lst):
    """ Return a list where all elemts are items. Any encountered list will be
    expanded.

    """
    result = list()
    for x in lst:
        if isinstance(x, list):
            for y in x:
                result.append(y)
        else:
            if x is not None: result.append(x)
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

    def visit_placeholder(self, node):
        if node.value: node.value.accept(self)
        else: self.text += str(self.id)
        self.text += ' '

    def visit_clause(self, node):
        # do a bit of coordination
        get_log().debug('Clause is "{0}"'.format(repr(node)))
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
        get_log().debug('VP is "{0}"'.format(repr(node)))
        get_log().debug('  head of VP is "{0}"'.format(head))
        modals = [f for f in lexicon.Modal.values]
        get_log().warning('Modals: {}'.format(modals))
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
        elif (head == 'be' or head == 'is'):
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


def simpleNlg_realisation(struct):
    """ Use the simpleNLG server to create a surface realisation of an Element.

    """
    v = XmlVisitor()
    struct.accept(v)
    get_log().debug('XML for realisation:\n{0}'.format(v.to_xml()))
    result = nlglib.nlg.simplenlg_client.xml_request(v.to_xml())
    return result.replace(' ,', ',')

def simple_realisation(struct):
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



#    There are constraints on the combination of phrases in E0:
#    The subject and the predicate must agree on number and person: if
#    the subject is a third person singular, so must the verb be. Objects complement only – and all – the transitive verbs.
#    When a pronoun is used, it is in the nominative case if it is in the subject position, and in the accusative case if it is an object.


############################################################################
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
############################################################################
