import hashlib
import os

THIS_FILE_DIR = os.path.dirname(os.path.realpath(__file__))
REPO_DIR = os.path.dirname(THIS_FILE_DIR)
EXAMPLES_DIR = os.path.join(REPO_DIR, 'examples')

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

