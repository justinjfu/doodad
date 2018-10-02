"""An os module wrapper for remote services.

A wrapper around python's os module which interfaces with various remote
filesystems such as S3, SSH, GCS, etc. 
"""
import os

import doodad.dfile.s3_file as s3_file
import doodad.dfile.ssh_file as ssh_file
import doodad.dfile.http_file as http_file


def _get_module(filename, os_path=False):
    if filename.startswith('ssh://'):
        return ssh_file
    elif filename.startswith('s3://'):
        return s3_file
    elif filename.startswith('http://') or filename.startswith('https://'):
        return http_file
    else:
        if os_path:
            return os.path
        else:
            return os


def open(filename, mode='r', **kwargs):
    """

    If filename begins with the prefix:
        "s3://path" Amazon S3
        "user@hostname:path" SSH file
    """
    module = _get_module(filename)
    return module.open(filename, mode=mode, **kwargs)


def mkdir(path, mode=0o777):
    """Create a directory named path with numeric mode mode."""
    module = _get_module(path)
    return module.mkdir(path, mode=mode)


def rmdir(path):
    """
    Remove (delete) the directory path. Only works when the directory is empty, 
    otherwise, OSError is raised.
    """
    module = _get_module(path)
    return module.rmdir(path)


def makedirs(path, mode=0o777, exist_ok=False):
    """Recursive directory creation function. Like mkdir(), but makes all
    intermediate-level directories needed to contain the leaf directory.
    """
    module = _get_module(path)
    return module.makedirs(path, mode=mode, exist_ok=exist_ok)


def listdir(path='.'):
    """
    Return a list containing the names of the entries in the directory given by path.
    The list is in arbitrary order, and does not include the special entries '.'
    and '..' even if they are present in the directory.
    """
    module = _get_module(path)
    return module.listdir(path)


def remove(path):
    """
    Remove (delete) the file path. If path is a directory, OSError is raised. 
    Use rmdir() to remove directories.
    """
    module = _get_module(path)
    return module.remove(path)


def exists(path):
    """Return True if path refers to an existing path."""
    module = _get_module(path, os_path=True)
    return module.exists(path)


def isfile(path):
    """Return True if path is an existing regular file."""
    module = _get_module(path, os_path=True)
    return module.isfile(path)


def isdir(path):
    """Return True if path is an existing directory."""
    module = _get_module(path, os_path=True)
    return module.isdir(path)
