import six
import re

from doodad.utils import safe_import
gcs = safe_import.try_import('cloudstorage')
storage = safe_import.try_import('google.cloud.storage')

GCS_REGEX = r'gs://(?P<bucket>[a-zA-Z0-9\-]+)/(?P<path>.*)'
GCS_REGEX = re.compile(GCS_REGEX)


def retry_params():
    return gcs.RetryParams(backoff_factor=1.1)


def to_gcp_path(filename):
    if filename.startswith('gs://'):
        return filename[4:]
    return filename


def open(filename, mode='r', **kwargs):
    #match = GCS_REGEX.match(filename)
    #bucket = match.get('bucket')
    #path = match.get('path')

    gcs_file = gcs.open(to_gcp_path(filename),
                    mode,
                    content_type='text/plain',
                    options={'x-goog-meta-foo': 'foo',
                            'x-goog-meta-bar': 'bar'},
                    retry_params=retry_params())
    return gcs_file

def mkdir(path, mode=0o777):
    raise ValueError()

def rmdir(path):
    raise ValueError()

def makedirs(path, mode=0o777, exist_ok=False):
    raise ValueError()

def listdir(path):
    gcs.listbucket(to_gcp_path(path), retry_params=retry_params())

def remove(path):
    gcs.delete(to_gcp_path(path), retry_params=retry_params())

def copy(src, dst):
    gcs.copy2(to_gcp_path(src),
              to_gcp_path(dst), 
              retry_params=retry_params())

def exists(path):
    raise ValueError()

def isfile(path):
    raise ValueError()

def isdir(path):
    raise ValueError()
