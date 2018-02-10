""" This package provides functionality for surface realising NLG Elements.

The only supported format at the moment is text although the future versions
should contain support for HTML (and possibly other useful formats such as ODF).

The input is a document where NLG Elements were already realised to strings.

"""

import logging

from nlglib.microplanning import *

from . import SimplenlgClient
from ..basic import Realiser as BasicRealiser


__all__ = ['Realiser']


class Realiser(BasicRealiser):

    def __init__(self, client=None, host='localhost', port=40000, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.client = client if client else SimplenlgClient(host, port)

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
