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
from ..basic import Realiser as BasicRealiser


class Realiser(BasicRealiser):

    def __init__(self, client=None, host='localhost', port=40000, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.client = client if client else SimplenlgClient(host, port)

    def __call__(self, msg, **kwargs):
        return self.realise(msg, **kwargs)

    def realise(self, msg, **kwargs):
        if msg is None:
            return ''
        elif msg.category in category.element_category:
            return self.element(msg, **kwargs)
        elif isinstance(msg, (list, set, tuple)) or msg.category == category.ELEMENT_LIST:
            return self.element_list(msg, **kwargs)
        elif msg.category == category.MSG:
            return self.message_specification(msg, **kwargs)
        elif msg.category == category.RST:
            return self.rst_relation(msg, **kwargs)
        elif msg.category == category.DOCUMENT:
            return self.document(msg, **kwargs)
        elif msg.category == category.PARAGRAPH:
            return self.paragraph(msg, **kwargs)
        else:
            return msg.realise(self, **kwargs) if hasattr(msg, 'realise') else str(msg)

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
