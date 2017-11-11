import logging

from nlglib.structures import *
from nlglib.microplanning import XmlVisitor

from ..simplenlg import simplenlg_client, SimplenlgClient

""" This package provides functionality for surface realising NLG Elements.

The only supported format at the moment is text although the future versions
should contain support for HTML (and possibly other useful formats such as ODF).

The input is a document where NLG Elements were already realised to strings.

"""

logger = logging.getLogger(__name__)


def realise(msg, **kwargs):
    """ Perform lexicalisation on the message depending on the type. """
    if msg is None:
        return None
    elif isinstance(msg, str):
        return msg
    elif isinstance(msg, Element):
        return realise_element(msg, **kwargs)
    elif isinstance(msg, MsgSpec):
        return realise_element(msg, **kwargs)
    elif isinstance(msg, (list, tuple)):
        return realise_list(msg, **kwargs)
    elif isinstance(msg, Message):
        return realise_message(msg, **kwargs)
    # elif isinstance(msg, Paragraph):
    #     return realise_paragraph(msg, **kwargs)
    # elif isinstance(msg, Section):
    #     return realise_section(msg, **kwargs)
    elif isinstance(msg, Document):
        return realise_document(msg, **kwargs)
    else:
        raise TypeError('"%s" is neither a Message nor a MsgInstance (%s)' %
                        (msg, type(msg)))


def realise_element(elt, **kwargs):
    """ Use the simpleNLG server to create a surface realisation of an Element.

    """
    if not elt.string:
        return ''
    v = XmlVisitor()
    elt.accept(v)
    logger.debug('XML for realisation:\n{0}'.format(v.to_xml()))
    result = kwargs.get('client', simplenlg_client).xml_request(v.to_xml())
    return result.replace(' ,', ',')


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
    sats = realise(msg.satellite, **kwargs)
    nucl = [realise(x, **kwargs) for x in msg.nuclei if x is not None]
    #    if len(sats) > 0:
    #        sats[0].add_front_modifier(Word(msg.marker, 'ADV'))
    sentences = _flatten(nucl + [sats])
    logger.debug('flattened sentences: %s' % sentences)
    # TODO: this si wrong because the recursive call can apply capitalisation
    # and punctuation multiple times...
    sentences = list(map(lambda e: e[:1].upper() + e[1:] +
                                   ('.' if e[-1] != '.' else ''),
                         [s for s in sentences if s != '']))
    return sentences


# def realise_paragraph(msg, **kwargs):
#     """ Return a copy of Paragraph with strings. """
#     logger.debug('Realising paragraph.')
#     if msg is None:
#         return None
#     messages = [realise(x, **kwargs) for x in msg.messages]
#     messages = _flatten(messages)
#     return Paragraph(*messages)
#
#
# def realise_section(msg, **kwargs):
#     """ Return a copy of a Section with strings. """
#     logger.debug('Realising section.')
#     if msg is None:
#         return None
#     title = realise(msg.title, **kwargs)
#     paragraphs = [Paragraph(realise(x, **kwargs)) for x in msg.content]
#     return Section(title, *paragraphs)


def realise_document(msg, **kwargs):
    """ Return a copy of a Document with strings. """
    logger.debug('Realising document.')
    if msg is None:
        return None
    title = realise(msg.title, **kwargs)
    sections = [realise(x, **kwargs) for x in msg.sections]
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
