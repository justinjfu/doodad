"""
"""
import six

def open(filename, mode='r', **kwargs):
    if mode != 'r':
        raise ValueError("HTTP files only support reading. Requested mode: %s" % mode)
    return HTTPFile(filename, **kwargs)

class HTTPFile(object):
    def __init__(self, filename, **kwargs):
        self._path = filename
        self._fp = six.moves.urllib.request.urlopen(filename, **kwargs)

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def __iter__(self):
        return self._fp.__iter__()
    
    def __getattr__(self, attr):
        return getattr(self._fp, attr)

def mkdir(path, mode=0o777):
    raise ValueError()

def rmdir(path):
    raise ValueError()

def makedirs(path, mode=0o777, exist_ok=False):
    raise ValueError()

def listdir(path='.'):
    raise ValueError() 

def remove(path):
    raise ValueError()

def exists(path):
    raise ValueError()

def isfile(path):
    raise ValueError()

def isdir(path):
    raise ValueError()
