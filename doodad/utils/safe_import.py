import contextlib
import importlib

class FailedImportModule(object):
    """
    A delayed failed import.
    This will error when you try to use something from the module,
    rather than when you import.

    Args:
        name (str): A module name
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
    """
    A wrapper around the import statement which
    delays ImportErrors until a function is used.
    This saves writing try-catch statements around optional libraries.

    Example usage:

    # This will not throw an ImportError immediately
    badmodule = try_import('badmodule')
    badmodule.badsubmodule = try_import('badmodule.badsubmodule')

    # This will now throw an import error
    badmodule.badsubmodule.badfunction()


    Args:
        name (str): Name of module
    Returns:
        Either a module if the import was successful, or a
        FailedImportModule if the package does not exist.
    """
    try:
        return importlib.import_module(name)
    except ImportError:
        return FailedImportModule(name)
    
