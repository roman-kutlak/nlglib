import os
import threading

# sentinel
_missing = object()


# remove multiple spaces
def trim(text):
    return ' '.join(text.strip().split())


def flatten(lst):
    """ Return a list where all elemts are items.
    Any encountered iterable will be expanded. Method is recursive.

    """
    result = []
    for x in lst:
        if isinstance(x, (tuple, list)):
            for y in flatten(x):
                result.append(y)
        else:
            if x is not None:
                result.append(x)
    return result


def total_seconds(td):
    """Returns the total seconds from a timedelta object.
    :param timedelta td: the timedelta to be converted in seconds
    :returns: number of seconds
    :rtype: int
    """
    return td.days * 60 * 60 * 24 + td.seconds


class LogPipe(threading.Thread):
    """ A pipe that runs in a separate thread and logs incoming messages.
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
