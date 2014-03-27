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


import logging

from nlg.structures import *

""" This package provides functionality for formatting NLG Elements. 

The only supported format at the moment is text although the future versions
should contain support for HTML (and possibly other useful formats such as ODF).

The input is a document where NLG Elements were already realised to strings.

"""


logging.getLogger(__name__).addHandler(logging.NullHandler())

def get_log():
    return logging.getLogger(__name__)


def to_text(element):
    """ return formatted element. """
    if element is None: return ''
    elif isinstance(element, str): return element
    elif isinstance(element, list): return to_text_list(element)
    elif isinstance(element, Message): return to_text_message(element)
    elif isinstance(element, Paragraph): return to_text_paragraph(element)
    elif isinstance(element, Section): return to_text_section(element)
    elif isinstance(element, Document): return to_text_document(element)
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
    return str(msg)


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

