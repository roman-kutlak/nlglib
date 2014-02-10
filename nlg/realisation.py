import itertools

from nlg.structures import *

""" This package provides functionality for surface realising NLG Elements.

The only supported format at the moment is text although the future versions
should contain support for HTML (and possibly other useful formats such as ODF).

The input is a document where NLG Elements were already realised to strings.

"""

DEBUG = False

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
        raise TypeError('"%s" is neither a Message nor a MsgInstance')


def realise_element(elt):
    """ Realise NLG element. """
    if DEBUG: print('^^^ called realise element!')
#    return str(elt).strip()
    v = StrVisitor()
    elt.accept(v)
    return v.to_str()


def realise_message_spec(msg):
    """ Realise message specification - this should not happen """
    if DEBUG: print('*** called realise message spec!')
    return str(msg).strip()


def realise_message(msg):
    """ Return a copy of Message with strings. """
    if DEBUG: print('*** called realise message!')
    if msg is None: return None
    nucl = realise(msg.nucleus)
    sats = [realise(x) for x in msg.satelites if x is not None]
    sentences = _flatten([nucl] + sats)
    sentences = list(map(lambda e: e[:1].upper() + e[1:] + '.',
                         [s for s in sentences if s != '']))
    return sentences


def realise_paragraph(msg):
    """ Return a copy of Paragraph with strings. """
    if DEBUG: print('*** called realise paragraph!')
    if msg is None: return None
    messages = [realise(x) for x in msg.messages]
    messages = _flatten(messages)
    return Paragraph(*messages)


def realise_section(msg):
    """ Return a copy of a Section with strings. """
    if DEBUG: print('*** called realise section!')
    if msg is None: return None
    title = realise(msg.title)
    paragraphs = [Paragraph(realise(x)) for x in msg.paragraphs]
    return Section(title, *paragraphs)


def realise_document(msg):
    """ Return a copy of a Document with strings. """
    if DEBUG: print('*** called realise document!')
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









