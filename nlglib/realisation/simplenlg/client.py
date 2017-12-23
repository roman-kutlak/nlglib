import os
import socket
import struct
import subprocess
import threading
import time
import logging
import urllib.parse

from nlglib.utils import LogPipe


log = logging.getLogger(__name__)


class ServerError(Exception):
    pass


def hton(num):
    """ Convert an integer into a list of bytes (do host to network conv)."""
    return struct.pack('!I', num)


def ntoh(num):
    """ Convert a list of bytes into an int (do network to host conv)."""
    return struct.unpack('!I', num)[0]


class Socket:
    """ A smarter version of a socket that can send and receive data easily."""

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = None

    def connect(self):
        """ Connect to the server. This is called in 'with' block. """
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.socket.connect((self.host, self.port))
        except OSError as msg:
            self.socket.close()
            self.socket = None
            log.exception('Socket.connect() caught an exception: %s' % msg)
            raise

    def _send(self, msg, length):
        """ Send a sequence of bytes of the specified length. """
        total_sent = 0
        while total_sent < length:
            sent = self.socket.send(msg[total_sent:])
            if sent == 0:
                raise RuntimeError('Connection lost.')
            total_sent += sent
        return total_sent

    def _recv(self, length=0):
        """ Receive a sequence of bytes of the specified length. """
        msg = b''
        while len(msg) < length:
            chunk = self.socket.recv(length - len(msg))
            if chunk == b'':
                raise RuntimeError('Connection lost.')
            msg += chunk
        return msg

    def send_string(self, msg, encoding='utf-8'):
        """ Send a string message. """
        # first sent the length of the message
        msg_size = hton(len(msg))
        self._send(msg_size, len(msg_size))

        # now send the message
        msg_data = bytearray(msg, encoding)
        length = self._send(msg_data, len(msg_data))
        return length

    def recv_string(self, encoding='utf-8'):
        """ Read a string from the server. """
        # first read the length of the message
        length = ntoh(self._recv(4))  # 4 bytes for int

        # now read the message
        msg = self._recv(length)
        return msg.decode(encoding)

    def close(self):
        """ Close the connection, informing the server first."""
        try:
            # the following line causes socket.close() to throw an exception
            # self.socket.shutdown(socket.SHUT_RDWR)
            if self.socket is not None:
                self.socket.close()
        except OSError as e:
            log.exception(
                'Socket.close() caught an exception: %s' % str(e))
            raise

    # allow the use in 'with' statement
    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, type, value, traceback):
        self.close()


class SimplenlgClient:
    """ A class that acts as a client to a simplenlg server.
        The host and port are configured through the settings file.

    """

    def __init__(self, host, port):
        log.debug('Starting SimplenlgClient(%s:%s)' % (str(host), str(port)))
        self.host = host
        self.port = int(port)
        self.socket = Socket(self.host, self.port)

    def xml_request(self, data):
        with self.socket as sock:
            sock.send_string(data)
            result = sock.recv_string()
            if 'Exception: XML unmarshal error' == result:
                raise ServerError(result)
            # decode xml symbols
            return urllib.parse.unquote_plus(result, encoding='utf-8')


class SimpleNLGServer(threading.Thread):
    """ A class that can be used as a SimpleNLG server. The actual java server
    is started as a subprocess and listens on the port 50007 for incoming XML
    requests for realisation.

    As the server starts in a separate thread, it requires certain
    synchronisation. In particular, the caller should call the start() method
    after creating the object and wait for the startup to finish.

    """

    def __init__(self, jar_path, port):
        super(SimpleNLGServer, self).__init__()
        log.debug('Creating simpleNLG server (%s)' % jar_path)
        log.debug('simpleNLG server port: ' + str(port))
        if not os.path.exists(jar_path):
            msg = 'The simpleNLG jar file "{}" does not exist.'
            raise ServerError(msg.format(jar_path))
        self.jar_path = jar_path
        self.port = str(port)
        self.start_cv = threading.Condition()
        self.exit_cv = threading.Condition()
        self._ready = False
        self._shutdown = False
        self.error_log = LogPipe(logging.getLogger('nlglib.simplenlg.server').error)
        self.output_log = LogPipe(logging.getLogger('nlglib.simplenlg.server').debug)

    def start(self):
        """ Start the server (calling run() on a different thread) and wait for
        it to initialise.
        Note that the caller will block until the thread starts.

        """
        log.debug('Starting simpleNLG server (%s)' % self.jar_path)
        super(SimpleNLGServer, self).start()
        self._wait_for_startup()
        log.info('Server up and running (%s)', self.port)

    def run(self):
        """ Start up SimpleNLG server as a subprocess and wait until someone
        signals that the server should be shut down using do_shutdown().

        """
        args = ['java', '-Xmx512m', '-jar', self.jar_path, self.port]
        with self.error_log, self.output_log:
            with subprocess.Popen(args,
                                  stdin=subprocess.PIPE,
                                  stdout=self.output_log,
                                  stderr=self.error_log,
                                  universal_newlines=True) as proc:
                # use a condition variable to signal that the process is running
                time.sleep(1)
                self._signal_startup_done()
                self._wait_for_shutdown()
                try:
                    out, errs = proc.communicate('exit\n', timeout=5)
                    if out:
                        log.debug('Server output: "{0}"'.format(out))
                    if errs:
                        log.error('Server errors: "{0}"'.format(errs))
                except subprocess.TimeoutExpired:
                    proc.kill()

    def is_ready(self):
        """ Return true if the server is initialised. """
        with self.start_cv:
            ready = self._ready
        log.debug('SimpleNLG server (%s) is ready' % self.jar_path)
        return ready

    def wait_for_init(self):
        """ Block until server is ready. """
        log.debug('SimpleNLG server (%s): waiting for init...' % self.jar_path)
        self._wait_for_startup()
        log.debug('SimpleNLG server (%s): init done.' % self.jar_path)

    def _wait_for_startup(self):
        """ Wait for the subprocess to start. """
        log.debug('SimpleNLG server (%s): waiting for startup...' % self.jar_path)
        with self.start_cv:
            while not self._ready:
                self.start_cv.wait()        
        log.debug('SimpleNLG server (%s): startup done.' % self.jar_path)

    def _wait_for_shutdown(self):
        """Block until self._shutdown is set to true (by calling shutdown())."""
        log.debug('SimpleNLG server (%s): is up and running...' % self.jar_path)
        with self.exit_cv:
            while not self._shutdown:
                self.exit_cv.wait()

    def _signal_startup_done(self):
        """ Set self._ready to True to signal that the server is running. """
        with self.start_cv:
            self._ready = True
            self.start_cv.notify()
        log.debug('SimpleNLG server (%s): signalling startup done.' % self.jar_path)

    def _signal_shutdown(self):
        """ Signal to the server that it should shut down the subprocess (the
        actual SimpleNLG server running in java virtual machine.

        """
        with self.exit_cv:
            self._shutdown = True
            self.exit_cv.notify()
        log.debug('SimpleNLG server (%s): signalling shutdown done.' % self.jar_path)

    def shutdown(self):
        """ Signal the server that it should shut down and wait for it.
        Note that the caller of this method will block until the server exits.

        """
        log.debug('Shutting down simpleNLG server (%s)' % self.jar_path)
        self._signal_shutdown()
        self.join()
