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


from copy import deepcopy
import logging
import re

from nlg.structures import *
import nlg.aggregation as aggregation
import nlg.lexicalisation as lexicalisation
import nlg.reg as reg
import nlg.realisation as realisation
import nlg.format as format

from utils import get_log

get_log().addHandler(logging.NullHandler())


class Nlg:
    def __init__(self):
        pass

    def process_nlg_doc(self, doc, ontology, context=None):
        get_log().debug('Processing document.')
        if context is None:
            get_log().debug('Creating new context for REG')
            context = reg.Context(ontology)
        summary = self.lexicalise(doc)
        get_log().debug('After lex: %s' % repr(summary))
        summary = self.aggregate(summary, 3)
        get_log().debug('After aggr: %s' % repr(summary))
        summary = self.generate_re(summary, context)
        get_log().debug('After REG: %s' % repr(summary))
        summary = self.realise(summary)
        get_log().debug('After realisation: %s' % repr(summary))
        summary = self.format(summary)
        get_log().debug('After formatting: %s' % repr(summary))
        return summary

    def process_nlg_doc2(self, doc, ontology, context=None):
        get_log().debug('Processing document v2.')
        summary = doc
        if context is None:
            get_log().debug('Creating new context for REG')
            context = reg.Context(ontology)
        summary = self.lexicalise(summary)
        get_log().debug('After lex: %s' % repr(summary))
        summary = self.aggregate(summary, 3)
        get_log().debug('After aggr: %s' % repr(summary))
        summary = self.generate_re(summary, context)
        get_log().debug('After REG: %s' % repr(summary))
        summary = self.realise2(summary)
        get_log().debug('After realisation: %s' % repr(summary))
        summary = self.format(summary)
        get_log().debug('After formatting: %s' % repr(summary))
        return summary

    def lexicalise(self, msgs):
        """ Lexicalise the given high-level structure using lexicalise
        from the lexicalisation package.
        
        """
        res = lexicalisation.lexicalise(msgs)
        return res

    def aggregate(self, msgs, limit):
        """ Run the messages through aggregation. """
        res = aggregation.aggregate(msgs, limit)
        return res

    def generate_re(self, msgs, context):
        """ Generate referring expressions. """
        res = reg.generate_re(msgs, context)
        return res

    def realise(self, msgs):
        """ Perform linguistic realisation. """
        res = realisation.realise(msgs)
        return res

    def realise2(self, msgs):
        """ Perform linguistic realisation using simpleNLG. """
        r = realisation.Realiser()
        res = r.realise(msgs)
        return res

    def format(self, msgs, fmt='txt'):
        """ Convert the realised messages to given format. Text by default. """
        text = format.to_text(msgs)
        return text



