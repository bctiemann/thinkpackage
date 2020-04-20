import threading, os
from collections import defaultdict
import logging


class ProcessSafeHandlerMixin():
    def __init__(self):
        super().__init__()

        self._locks = defaultdict(lambda: threading.RLock())

    def acquire(self):
        current_process_id = current_process().pid
        self._locks[current_process_id].acquire()

    def release(self):
        current_process_id = current_process().pid
        self._locks[current_process_id].release()


class NullHandler(ProcessSafeHandlerMixin, logging.NullHandler):
    pass

class StreamHandler(ProcessSafeHandlerMixin, logging.StreamHandler):

    def __init__(self, stream=None):
        """
        Initialize the handler.

        If stream is not specified, sys.stderr is used.
        """
        logging.Handler.__init__(self)
        if stream is None:
            stream = sys.stderr
        self.stream = stream


class FileHandler(ProcessSafeHandlerMixin, logging.FileHandler):

    def __init__(self, filename, mode='a', encoding=None, delay=False):
        """
        Open the specified file and use it as the stream for logging.
        """
        # Issue #27493: add support for Path objects to be passed in
        filename = os.fspath(filename)
        #keep the absolute path, otherwise derived classes which use this
        #may come a cropper when the current directory changes
        self.baseFilename = os.path.abspath(filename)
        self.mode = mode
        self.encoding = encoding
        self.delay = delay
        if delay:
            #We don't open the stream, but we still need to call the
            #Handler constructor to set level, formatter, lock etc.
            logging.Handler.__init__(self)
            self.stream = None
        else:
            StreamHandler.__init__(self, self._open())
