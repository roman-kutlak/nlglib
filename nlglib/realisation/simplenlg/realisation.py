""" This package provides functionality for surface realising NLG Elements.

The only supported format at the moment is text although the future versions
should contain support for HTML (and possibly other useful formats such as ODF).

The input is a document where NLG Elements were already realised to strings.

"""

import logging

from nlglib.microplanning import *
from nlglib.macroplanning import *
from nlglib.utils import flatten

from . import SimplenlgClient


class Realiser(object):

    def __init__(self, client=None, host='localhost', port=40000, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.client = client if client else SimplenlgClient(host, port)

    def __call__(self, msg, **kwargs):
        return self.realise(msg, **kwargs)

    def realise(self, msg, **kwargs):
        if msg is None:
            return ''
        elif isinstance(msg, str):
            return msg
        elif isinstance(msg, Element):
            return self.element(msg, **kwargs)
        elif isinstance(msg, MsgSpec):
            return self.message_spec(msg, **kwargs)
        elif isinstance(msg, (list, tuple)):
            return self.list(msg, **kwargs)
        elif isinstance(msg, Message):
            return self.message(msg, **kwargs)
        elif isinstance(msg, Document):
            return self.document(msg, **kwargs)
        else:
            raise TypeError('"%s" is neither a Message nor a MsgInstance' % type(msg))

    def element(self, elt, **kwargs):
        """ Realise NLG element. """
        self.logger.debug('Realising element:\n{0}'.format(repr(elt)))
        if not elt.string:
            return ''
        v = XmlVisitor()
        elt.accept(v)
        self.logger.debug('XML for realisation:\n{0}'.format(v.to_xml()))
        result = self.client.xml_request(v.to_xml())
        return result.replace(' ,', ',')

    def message_spec(self, msg, **kwargs):
        """ Realise message specification - this should not happen """
        self.logger.debug('Realising message spec:\n{0}'.format(repr(msg)))
        return str(msg).strip()

    def list(self, elt, **kwargs):
        """ Realise a list. """
        self.logger.debug('Realising list of elements:\n{0}'.format(repr(elt)))
        return ' '.join(self.realise(x, **kwargs) for x in elt)

    def message(self, msg, **kwargs):
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
        return Document(*sections, title=title)
