#############################################################################
##
## Copyright (C) 2013 Roman Kutlak, University of Aberdeen.
## All rights reserved.
##
## This file is part of SAsSy NLG library.
##
## You may use this file under the terms of the BSD license as follows:
##
## "Redistribution and use in source and binary forms, with or without
## modification, are permitted provided that the following conditions are
## met:
##   * Redistributions of source code must retain the above copyright
##     notice, this list of conditions and the following disclaimer.
##   * Redistributions in binary form must reproduce the above copyright
##     notice, this list of conditions and the following disclaimer in
##     the documentation and/or other materials provided with the
##     distribution.
##   * Neither the name of University of Aberdeen nor
##     the names of its contributors may be used to endorse or promote
##     products derived from this software without specific prior written
##     permission.
##
## THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
## "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
## LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
## A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
## OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
## SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
## LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
## DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
## THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
## (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
## OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."
##
#############################################################################


import itertools
import logging

from nlg.structures import *


""" This package provides functionality for surface realising NLG Elements.

The only supported format at the moment is text although the future versions
should contain support for HTML (and possibly other useful formats such as ODF).

The input is a document where NLG Elements were already realised to strings.

"""


logging.getLogger(__name__).addHandler(logging.NullHandler())

def get_log():
    return logging.getLogger(__name__)


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
    get_log().debug('Realising element.')
#    return str(elt).strip()
    v = StrVisitor()
    elt.accept(v)
    return v.to_str()


def realise_message_spec(msg):
    """ Realise message specification - this should not happen """
    get_log().debug('Realising message spec.')
    return str(msg).strip()


def realise_message(msg):
    """ Return a copy of Message with strings. """
    get_log().debug('Realising message.')
    if msg is None: return None
    nucl = realise(msg.nucleus)
    sats = [realise(x) for x in msg.satelites if x is not None]
    sentences = _flatten([nucl] + sats)
    sentences = list(map(lambda e: e[:1].upper() + e[1:] + '.',
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









