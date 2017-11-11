import logging

from .client import SimplenlgClient, SimpleNLGServer

simplenlg_client = None
simplenlg_server = None

logger = logging.getLogger(__name__)


def init(jar, host, port, server=True, client=True):
    """ Initialise the simpleNLG client and server. """
    logger.info('Initialising simpleNLG server using info: '
                '\n\tjar: "{0}" \n\thost" "{1}" \n\tport: "{2}"'
                .format(jar, host, port))
    if not port:
        logger.warning('Using default port "50007"')
        port = 50007
    if server:
        global simplenlg_server
        if not jar:
            logger.error('SimpleNLG jar not specified.')
            logger.error('Initialisation of nlg server failed.')
            import os
            logger.error('CWD: ' + os.getcwd())
            raise Exception('Initialisation of nlg server failed.')
        if simplenlg_server:
            logger.warning('Initialising SimpleNLG Server when a server is '
                           'already running. Shutting down the previous instance.')
            shutdown(True, False)
        simplenlg_server = SimpleNLGServer(jar, port)
        simplenlg_server.start()
    if client:
        global simplenlg_client
        if not host:
            logger.warning('Using default host "localhost"')
            host = 'localhost'
        if simplenlg_client:
            logger.warning('Initialising SimpleNLG Client when a client is '
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


if not simplenlg_client:
    simplenlg_client = SimplenlgClient(host='localhost', port=50007)

from .realisation import *
