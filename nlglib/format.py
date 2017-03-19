import logging

from nlglib.structures import *

""" This package provides functionality for formatting NLG Elements.

The only supported format at the moment is text although the future versions
should contain support for HTML (and possibly other useful formats such as ODF).

The input is a document where NLG Elements were already realised to strings.

"""

logging.getLogger(__name__).addHandler(logging.NullHandler())


def get_log():
    return logging.getLogger(__name__)


def to_text(element, **kwargs):
    """ return formatted element. """
    if element is None:
        return ''
    elif isinstance(element, str):
        return element
    elif isinstance(element, list):
        return to_text_list(element)
    elif isinstance(element, Message):
        return to_text_message(element)
    elif isinstance(element, Paragraph):
        return to_text_paragraph(element)
    elif isinstance(element, Section):
        return to_text_section(element)
    elif isinstance(element, Document):
        return to_text_document(element)
    else:
        get_log().warning('Unexpected type in format.to_text(): %s'
                          % repr(element))
        return str(element)


def to_text_list(messages):
    """ Realise individual elements of the list. """
    get_log().debug('Formatting list.')
    text = ' '.join([to_text(x) for x in messages])
    return text.strip()


def to_text_message(msg):
    get_log().debug('Formatting message(%s).' % repr(msg))
    # FIXME: here needs to be some logic to join a rhetorical relation into a sentence
    # for example, add the marker to the front, then nucleus, then satellites joined with 'and'
    if msg.marker in ('however', 'although'):
        pattern = '{marker}, {nucleus}'
    elif msg.marker in ('but', 'and', 'or'):
        pattern = '{nucleus} {marker}'
    else:
        pattern = '{nucleus}'
    sentence = pattern.format(nucleus=to_text(msg.nucleus), marker=msg.marker)
    if msg.satellites:
        sentence += ' ' + ' and '.join(to_text(s).strip() for s in msg.satellites)
    sentence = sentence[0].upper() + sentence[1:] + ('.' if sentence[-1] not in '?!.;' else '')
    return sentence


def to_text_paragraph(para):
    """ Take the realised sentences and add tab at the beginning. """
    get_log().debug('Formatting paragraph.')
    text = ' '.join([to_text(x) for x in para.messages])
    return '    ' + text.strip()


def to_text_section(sec):
    """ Convert a section to text. """
    get_log().debug('Formatting section.')
    text = (to_text(sec.title) + '\n'
            + '\n'.join([to_text(p) for p in sec.paragraphs]))
    return text


def to_text_document(doc):
    """ Convert a document to text. """
    get_log().debug('Formatting document.')
    text = (to_text(doc.title) + '\n'
            + '\n'.join([to_text(s) for s in doc.sections]))
    return text
