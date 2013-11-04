from nlg.structures import *

""" This package provides functionality for surface realising NLG Elements.

The only supported format at the moment is text although the future versions
should contain support for HTML (and possibly other useful formats such as ODF).

The input is a document where NLG Elements were already realised to strings.

"""



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


# TODO: lexicalisation should replace Messages by NLG Elements

def realise_element(elt):
    """ Realise NLG element. """
#    print('^^^ called realise message spec!')
    return str(elt).strip()


def realise_message_spec(msg):
    """ Realise message specification - this should not happen """
    print('*** called realise message spec!')
    return str(msg).strip()


def realise_message(msg):
    """ Return a copy of Message with strings. """
    if msg is None: return None
    data = [realise(x) for x in
            ([msg.nucleus] + msg.satelites) if x is not None ]
    return ' '.join(data).strip()


def realise_paragraph(msg):
    """ Return a copy of Paragraph with strings. """
    if msg is None: return None
    messages = [realise(x) for x in msg.messages if x is not None]
    return Paragraph(*messages)


def realise_section(msg):
    """ Return a copy of a Section with strings. """
    if msg is None: return None
    title = realise(msg.title)
    paragraphs = [Paragraph(realise(x)) for x in msg.paragraphs if x is not None]
    return Section(title, *paragraphs)


def realise_document(msg):
    """ Return a copy of a Document with strings. """
    if msg is None: return None
    title = realise(msg.title)
    sections = [realise(x) for x in msg.sections if x is not None]
    return Document(title, *sections)











