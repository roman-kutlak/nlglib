import logging

from nlglib.simplenlg import SimplenlgClient, SimpleNLGServer
from nlglib.structures import *
from nlglib import aggregation
from nlglib import lexicalisation
from nlglib import reg
from nlglib import realisation
from nlglib import format
from nlglib.reg import Context


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
        # check if context has templates and if so, use them
        if hasattr(context, 'templates'):
            for name, tplt in context.templates.items():
                lexicalisation.add_template(name, tplt)
        summary = doc
        if context is None:
            get_log().debug('Creating new context for REG')
            context = reg.Context(ontology)
        summary = self.lexicalise(summary)
        get_log().debug('After lex: \n%s' % repr(summary))
        summary = self.aggregate(summary, 3)
        if isinstance(summary, (list, tuple)):
            summary = Paragraph(*summary)

        get_log().debug('After aggr: \n%s' % repr(summary))
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


# def init_from_settings(settings_path='resources/simplenlg.settings',
#          server=True, client=True):
#     """ Initialise the simpleNLG client and server using a settings file. """
#     get_log().info('Initialising simpleNLG server from settings in "{0}"'
#                    .format(settings_path))
#     s = Settings(settings_path)
#     port = s.get_setting('SimplenlgPort')
#     if not port:
#         get_log().error('Could not find value for '
#                         'SimplenlgPort in settings.')
#         port = None
#     if server:
#         jar  = s.get_setting('SimplenlgJarPath')
#         if jar is None:
#             get_log().error('Could not find value for '
#                             'SimplenlgJarPath in settings.')
#             jar = None
#     if client:
#         host = s.get_setting('SimplenlgHost')
#         if host is None:
#             get_log().error('Could not find value for '
#                             'SimplenlgHost in settings.')
#     init(jar, host, port)


def init(jar, host, port, server=True, client=True):
    """ Initialise the simpleNLG client and server. """
    get_log().info('Initialising simpleNLG server using info: '
                   '\n\tjar: "{0}" \n\thost" "{1}" \n\tport: "{2}"'
                   .format(jar, host, port))
    if not port:
        get_log().warning('Using default port "50007"')
        port = 50007
    if server:
        global simplenlg_server
        if not jar:
            get_log().error('SimpleNLG jar not specified.')
            get_log().error('Initialisation of nlg server failed.')
            import os
            get_log().error('CWD: ' + os.getcwd())
            raise Exception('Initialisation of nlg server failed.')
        if simplenlg_server:
            get_log().warning('Initialising SimpleNLG Server when a server is '
                              'already running. Shutting down the previous instance.')
            shutdown(True, False)
        simplenlg_server = SimpleNLGServer(jar, port)
        simplenlg_server.start()
    if client:
        global simplenlg_client
        if not host:
            get_log().warning('Using default host "localhost"')
            host = 'localhost'
        if simplenlg_client:
            get_log().warning('Initialising SimpleNLG Client when a client is '
                              'already running. Shutting down the previous instance.')
            shutdown(False, True)
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
