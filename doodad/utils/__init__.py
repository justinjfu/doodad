import os
import hashlib

_UTILS_DIR = os.path.dirname(os.path.realpath(__file__))
PKG_DIR = os.path.dirname(_UTILS_DIR)
REPO_DIR = os.path.dirname(PKG_DIR)
TESTING_DIR = os.path.join(REPO_DIR, 'testing')
SCRIPTS_DIR = os.path.join(REPO_DIR, 'scripts')

HASH_BUF_SIZE = 65536 

def hash_file(filename):
    hasher = hashlib.md5()
    with open(filename, 'rb') as f:
        while True:
            data = f.read(HASH_BUF_SIZE)
            if not data:
                break
            hasher.update(data)
    return hasher.hexdigest()
