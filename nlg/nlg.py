import logging

from nlg.simplenlg import SimplenlgClient, SimpleNLGServer
from nlg.structures import *
import nlg.aggregation as aggregation
import nlg.lexicalisation as lexicalisation
import nlg.reg as reg
import nlg.realisation as realisation
import nlg.format as format
from nlg.utils import Settings
from nlg.reg import Context

def get_log():
    return logging.getLogger(__name__)

get_log().addHandler(logging.NullHandler())


simplenlg_server = None
simplenlg_client = None


class Nlg:
    def __init__(self):
        self.realiser = realisation.Realiser(simple=False)

    def process_nlg_doc(self, doc, ontology, context=None):
        if context is None: context = Context(ontology)
        get_log().debug('Processing document.')
        if context is None:
            get_log().debug('Creating new context for REG')
            context = reg.Context(ontology)
        summary = self.lexicalise(doc)
        get_log().debug('After lex:\n%s' % repr(summary))
        summary = self.aggregate(summary, 3)
        get_log().debug('After aggr:\n%s' % repr(summary))
        summary = self.generate_re(summary, context)
        get_log().debug('After REG:\n%s' % repr(summary))
        summary = self.realise(summary)
        get_log().debug('After realisation:\n%s' % repr(summary))
        summary = self.format(summary)
        get_log().debug('After formatting:\n%s' % repr(summary))
        return summary

    def process_nlg_doc2(self, doc, ontology, context=None):
        get_log().debug('Processing document v2.')
        summary = doc
        if context is None:
            get_log().debug('Creating new context for REG')
            context = reg.Context(ontology)
        summary = self.lexicalise(summary)
        get_log().debug('After lex: \n%s' % str(summary))
        summary = self.aggregate(summary, 3)
        get_log().debug('After aggr: \n%s' % str(summary))
        summary = self.generate_re(summary, context)
        get_log().debug('After REG: \n%s' % str(summary))
        summary = self.realise2(summary)
        get_log().debug('After realisation: \n%s' % str(summary))
        summary = self.format(summary)
        get_log().debug('After formatting: \n%s' % str(summary))
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
        res = self.realiser.realise(msgs)
        return res

    def format(self, msgs, fmt='txt'):
        """ Convert the realised messages to given format. Text by default. """
        text = format.to_text(msgs)
        return text


def init(settings_path='nlg/resources/simplenlg.settings',
         server=True, client=True):
    """ Initialise the simpleNLG client and server. """
    get_log().info('Initialising simpleNLG server from settings in "{0}"'
                   .format(settings_path))
    if server:
        global simplenlg_server
        s = Settings(settings_path)
        host = s.get_setting('SimplenlgHost')
        port = s.get_setting('SimplenlgPort')
        jar  = s.get_setting('SimplenlgJarPath')
        if host is None:
            get_log().error('Could not find value for '
                            'SimplenlgHost in settings.')
            get_log().warning('Using default host "localhost"')
            host = 'localhost'
        if port is None:
            get_log().error('Could not find value for '
                            'SimplenlgPort in settings.')
            get_log().warning('Using default port "50007"')
            port = 50007
        if jar is None:
            get_log().error('Could not find value for '
                            'SimplenlgJarPath in settings.')
            get_log().error('Initialisation of nlg server failed.')
            import os
            get_log().error('CWD: ' + os.getcwd())
        else:
            simplenlg_server = SimpleNLGServer(jar, port)
            simplenlg_server.start()
    if client:
        global simplenlg_client
        simplenlg_client = SimplenlgClient(host, port)


def shutdown(server=True, client=True):
    """ Shut down the simpleNLG client and server. """
    if server:
        global simplenlg_server
        if simplenlg_server is not None:
            simplenlg_server.shutdown()
            simplenlg_server = None
    if client:
        global simplenlg_client
        if simplenlg_client is not None:
            simplenlg_client = None


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
