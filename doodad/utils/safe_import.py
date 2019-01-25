import contextlib
import importlib

class FailedImportModule(object):
    """
    A delayed failed import.
    This will error when you try to use something from the module,
    rather than when you import.
    """
    def __init__(self, name):
        self.module_name = name
        self.submodules = {}
    
    def __getattr__(self, key):
        if key in self.submodules:
            return self.submodules[key]
        raise ImportError('Could not import %s' % self.module_name)

    def __setattr__(self, key, value):
        if isinstance(value, FailedImportModule):
            self.submodules[key] = value
        else:
            super(FailedImportModule, self).__setattr__(key, value)
        

def try_import(name):
    try:
        importlib.import_module(name)
    except ImportError:
        return FailedImportModule(name)
    
