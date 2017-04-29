import logging
from urllib.parse import unquote_plus

import nlglib
from nlglib.structures import *
from nlglib import lexicon, nlg
from nlglib.microplanning import XmlVisitor

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
        if msg is None:
            return None
        elif isinstance(msg, str):
            return msg
        elif isinstance(msg, Element):
            return self.realise_element(msg)
        elif isinstance(msg, MsgSpec):
            return self.realise_message_spec(msg)
        elif isinstance(msg, Message):
            return self.realise_message(msg)
        elif isinstance(msg, Paragraph):
            return self.realise_paragraph(msg)
        elif isinstance(msg, Section):
            return self.realise_section(msg)
        elif isinstance(msg, Document):
            return self.realise_document(msg)
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
            return elt

    def realise_message_spec(self, msg):
        """ Realise message specification - this should not happen """
        get_log().debug('Realising message spec:\n{0}'.format(repr(msg)))
        return str(msg).strip()

    def realise_message(self, msg):
        """ Return a copy of Message with strings. """
        get_log().debug('Realising message:\n{0}'.format(repr(msg)))
        if msg is None: return None
        nucl = self.realise(msg.nucleus)
        sats = [self.realise(x) for x in msg.satellites if x is not None]
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
        paragraphs = [Paragraph(self.realise(x)) for x in msg.content]
        return Section(title, *paragraphs)

    def realise_document(self, msg):
        """ Return a copy of a Document with strings. """
        get_log().debug('Realising document.')
        if msg is None: return None
        title = self.realise(msg.title)
        sections = [self.realise(x) for x in msg.sections]
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
            if x is not None:
                result.append(x)
    return result


def simpleNlg_realisation(struct, **kwargs):
    """ Use the simpleNLG server to create a surface realisation of an Element.

    """
    v = XmlVisitor()
    struct.accept(v)
    get_log().debug('XML for realisation:\n{0}'.format(v.to_xml()))
    result = nlg.simplenlg_client.xml_request(v.to_xml())
    return result.replace(' ,', ',')


# There are constraints on the combination of phrases in E0:
#    The subject and the predicate must agree on number and person: if
#    the subject is a third person singular, so must the verb be.
# Objects complement only – and all – the transitive verbs.
#    When a pronoun is used, it is in the nominative case
# if it is in the subject position, and in the accusative case
# if it is an object.
