from nlg.structures import *

""" This package provides functionality for formatting NLG Elements. 

The only supported format at the moment is text although the future versions
should contain support for HTML (and possibly other useful formats such as ODF).

The input is a document where NLG Elements were already realised to strings.

"""


def to_text(element):
    """ return formatted element. """
    if element is None: return ''
    elif isinstance(element, str): return element
    elif isinstance(element, Message): return to_text_message(element)
    elif isinstance(element, Paragraph): return to_text_paragraph(element)
    elif isinstance(element, Section): return to_text_section(element)
    elif isinstance(element, Document): return to_text_document(element)
    else:
        print('Unexpected type in format.to_text(): %s' % repr(element))
        return str(element)


def to_text_message(msg):
    print('___ called to_text_message(%s)' % repr(msg))
    return str(msg)


def to_text_paragraph(para):
    """ Take the realised sentences, capitalise first letter and add period. """
    # capitalise first letter
    text = list(map(lambda e: e[:1].upper() + e[1:],
                [m for m in para.messages if m is not None]))
    if len(text) == 0: return ''
    elif len(text) == 1: return text[0] + '.'
    else: text = '. '.join(text)
    return text.strip()


def to_text_section(sec):
    """ Convert a section to text. """
    text = (to_text(sec.title) + '\n'
            + '\n'.join([to_text(p) for p in sec.paragraphs if p is not None]))
    return text


def to_text_document(doc):
    """ Convert a document to text. """
    text = (to_text(doc.title) + '\n'
            + '\n'.join([to_text(s) for s in doc.sections if s is not None]))
    return text
