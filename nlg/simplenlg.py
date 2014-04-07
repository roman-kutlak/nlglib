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


import sys
import socket
import struct
import subprocess
import time
import threading
import logging
import traceback


logging.getLogger(__name__).addHandler(logging.NullHandler())

def get_log():
    return logging.getLogger(__name__)


simplenlg_path = 'nlg/resources/simplenlg.jar'


class ServerError(Exception): pass


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

    def connect(self):
        """ Connect to the server. This is called in 'with' block. """
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.socket.connect((self.host, self.port))
        except OSError as msg:
            self.socket.close()
            self.socket = None
            get_log().exception('Socket.connect() caught an exception: %s' % msg)
            raise

    def _send(self, msg, length):
        """ Send a sequence of bytes of the specified length. """
        total_sent = 0
        sent = -1
        while (total_sent < length):
            sent = self.socket.send(msg[total_sent:])
            if sent == 0:
                raise RuntimeError('Connection lost.')
            total_sent += sent
        return total_sent
    
    def _recv(self, length = 0):
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
        length = ntoh(self._recv(4)) # 4 bytes for int
    
        # now read the message
        msg = self._recv(length)
        return msg.decode(encoding)

    def close(self):
        """ Close the connection, informing the server first."""
        try:
        # the following line causes socket.close() to throw an exception
            #self.socket.shutdown(socket.SHUT_RDWR)
            if self.socket is not None:
                self.socket.close()
        except OSError as e:
            get_log().exception('Socket.close() caught an exception: %s' % str(e))
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
        self.host = host
        self.port = port
        self.socket = Socket(self.host, int(self.port))

    def xml_request(self, data):
        with self.socket as socket:
            socket.send_string(data)
            result = socket.recv_string()
            return result


class SimpleNLGServer(threading.Thread):
    """ A class that can be used as a SimpleNLG server. The actual java server
    is started as a subprocess and listens on the port 50007 for incoming XML
    requests for realisation.
    
    As the server starts in a separate thread, it requires certain 
    synchronisation. In particular, the caller should call the start() method
    after creating the object and wait for the startup to finish.
    
    """
    # TODO: add port or server config file or something
    def __init__(self, jar_path):
        super(SimpleNLGServer, self).__init__()
        get_log().debug('Starting simpleNLG server')
        self.jar_path = jar_path
        self.start_cv = threading.Condition()
        self.exit_cv = threading.Condition()
        self._ready = False
        self._shutdown = False

    def start(self):
        """ Start the server (calling run() on a different thread) and wait for
        it to initialise.
        Note that the caller will block until the thread starts.

        """
        super(SimpleNLGServer, self).start()
        self._wait_for_startup()

    def run(self):
        """ Start up SimpleNLG server as a subprocess and wait until someone
        signals that the server should be shut down using do_shutdown().
        
        """
        args = ['java', '-jar', self.jar_path, '-Xmx512MB']

        with subprocess.Popen(args, stdin=subprocess.PIPE,
                                universal_newlines=True) as proc:
            # use a condition variable to signal that the process is running
            time.sleep(1)
            self._signal_startup_done()
            self._wait_for_shutdown()

            try:
                out, errs = proc.communicate('exit\n', timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()

    def is_ready(self):
        """ Return true if the server is initialised. """
        ready = False
        self.start_cv.acquire()
        ready = self._ready
        self.start_cv.release()
        return ready

    def wait_for_init(self):
        """ Block until server is ready. """
        self._wait_for_startup()

    def _wait_for_startup(self):
        """ Wait for the subprocess to start. """
        self.start_cv.acquire()
        while not self._ready:
            self.start_cv.wait()
        self.start_cv.release()

    def _wait_for_shutdown(self):
        """ Block until self._shutdown is set to true (by calling shutdown())."""
        self.exit_cv.acquire()
        while not self._shutdown:
            self.exit_cv.wait()
        self.exit_cv.release()

    def _signal_startup_done(self):
        """ Set self._ready to True to signal that the server is running. """
        self.start_cv.acquire()
        self._ready = True
        self.start_cv.notify()
        self.start_cv.release()

    def _signal_shutdown(self):
        """ Signal to the server that it should shut down the subprocess (the 
        actual SimpleNLG server running in java virtual machine.
        
        """
        self.exit_cv.acquire()
        self._shutdown = True
        self.exit_cv.notify()
        self.exit_cv.release()

    def shutdown(self):
        """ Signal the server that it should shut down and wait for it.
        Note that the caller of this method will block until the server exits.

        """
        get_log().debug('Shutting down simpleNLG server')
        self._signal_shutdown()
        self.join()
#        import traceback
#        traceback.print_stack()
