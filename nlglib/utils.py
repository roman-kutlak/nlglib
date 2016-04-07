import os
import sys
import logging
import threading


def get_log():
    return logging.getLogger('nlg')


# remove multiple spaces
def trim(str):
    return ' '.join(str.strip().split())


class Settings:
    """ Class Settings reads a file with various settings such as paths to
        domain definition files, paths to file with plans, etc.

        """

    def __init__(self, filename):
        # assume the file contains key value pairs with no spaces
        self.table = dict()
        try:
            with open(filename) as f:
                for line in f:
                    kv = line.split()
                    if len(kv) > 1:
                        self.table[kv[0]] = kv[1]

        except FileNotFoundError as e:
            get_log().exception("Could not find settings file '%s'" % filename)
            raise e
        except IOError as e:
            get_log().exception("Something wrong with the file '%s'" % filename)
            raise e
            
    def get_setting(self, key, default=None):
        return self.table.get(key, default)

"""
    Look for a default settings file in $HOME/.sassy/sassy.prefs
    and create a Settings object using that file.

    """
def get_user_settings():
    home = os.getenv("HOME")
    path = os.sep.join([home, ".sassy/sassy.prefs"])
    return Settings(path)


def find_files(dir, extension):
    result = []
    for root, dirs, files in os.walk(dir):
        for file in files:
            if file.endswith(extension):
                 result.append( (root, file) )
    return result


class LogPipe(threading.Thread):
    """ A pipe that runs in a separate thread and logs comming messages.
    codereview.stackexchange.com/questions/6567/
    how-to-redirect-a-subprocesses-output-stdout-and-stderr-to-logging-module
    
    """
    
    def __init__(self, log_fn):
        """Setup the object with a logger and a loglevel
        and start the thread
        """
        threading.Thread.__init__(self)
        self.daemon = False
        self.log_fn = log_fn
        self.fdRead, self.fdWrite = os.pipe()
        self.pipeReader = os.fdopen(self.fdRead)

    def fileno(self):
        """Return the write file descriptor of the pipe
        """
        return self.fdWrite

    def run(self):
        """Run the thread, logging everything.
        """
        for line in iter(self.pipeReader.readline, ''):
            self.log_fn(line.strip('\n'))

        self.pipeReader.close()

    def close(self):
        """Close the write end of the pipe.
        """
        os.close(self.fdWrite)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False


# http://cx-freeze.readthedocs.org/en/latest/faq.html
def find_data_file(*path_chunks):
    if getattr(sys, 'frozen', False):
        # The application is frozen
        datadir = os.path.dirname(sys.executable)
    else:
        # The application is not frozen
        # Change this bit to match where you store your data files:
        datadir = os.path.dirname(__file__)
    return os.path.join(datadir, *path_chunks)


############################################################################
#
# Copyright (C) 2013 Roman Kutlak, University of Aberdeen.
# All rights reserved.
#
# This file is part of SAsSy NLG library.
#
# You may use this file under the terms of the BSD license as follows:
#
# "Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#   * Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in
#     the documentation and/or other materials provided with the
#     distribution.
#   * Neither the name of University of Aberdeen nor
#     the names of its contributors may be used to endorse or promote
#     products derived from this software without specific prior written
#     permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."
#
############################################################################
