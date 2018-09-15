import re

import doodad.dfile.s3_file as s3_file
import doodad.dfile.ssh_file as ssh_file

SSH_REGEX = '(?P<user>[a-zA-Z0-9_\-]+)@(?P<hostname>([a-zA-Z0-9_\-\.])+):(?P<path>.*)'
SSH_REGEX = re.compile(SSH_REGEX)

def open(filename, mode='r', **kwargs):
    """

    If filename begins with the prefix:
        "s3://path" Amazon S3
        "user@hostname:path" SSH file
    """
    if filename.startswith(r's3://'):
        return s3_file.open_s3_file(filename, mode=mode, **kwargs)

    if '@' in filename:
        ssh_match = SSH_REGEX.match(filename)
        if ssh_match:
            user = ssh_match.group('user')
            host = ssh_match.group('hostname')
            path = ssh_match.group('path')
            return ssh_file.open_ssh_file(path, user, host, mode=mode, **kwargs)
    return open(filename, mode=mode, **kwargs)


def parse_prefix(filename):
    if ssh_match:
        return SSH_FILE
    return None


