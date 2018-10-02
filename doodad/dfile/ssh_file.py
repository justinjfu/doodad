import re

from doodad.dfile import tmp_cache_file
from doodad.dfile import utils
from doodad.credentials import ssh as ssh_credentials
from doodad.utils import shell


SSH_REGEX = r'ssh://(?P<user>[a-zA-Z0-9_\-]+)@(?P<hostname>([a-zA-Z0-9_\-\.])+):(?P<path>.*)'
SSH_REGEX = re.compile(SSH_REGEX)


def _parse_filename(filename):
    ssh_match = SSH_REGEX.match(filename)
    if ssh_match:
        user = ssh_match.group('user')
        host = ssh_match.group('hostname')
        path = ssh_match.group('path')
        return user, host, path
    else:
        raise ValueError("Invalid SSH format: %s" % filename)


class SSHFile(tmp_cache_file.TmpCacheFile):
    def __init__(self, filename, user, host, mode):
        self.filename = filename
        self.username = user
        self.hostname = host
        self.credentials = ssh_credentials.get_credentials(host, user)
        super(SSHFile, self).__init__(mode=mode)

    def on_load(self):
        scp_cmd = self.credentials.get_scp_cmd(
            self.filename,
            self._tmp_file.name,
            src_remote=True)
        try:
            shell.call(scp_cmd, dry=False, wait=True, shell=True)
        except OSError:
            raise OSError("SSHFile failed on SCP cmd: %s" % scp_cmd)
        self._tmp_file.seek(0)

    def on_flush(self):
        scp_cmd = self.credentials.get_scp_cmd(
            self._tmp_file.name,
            self.filename,
            src_remote=False)
        try:
            shell.call(scp_cmd, dry=False, wait=True, shell=True)
        except OSError:
            raise OSError("SSHFile failed on SCP cmd: %s" % scp_cmd)


def _run_ssh_cmd(user, host, cmd, output=False):
    credentials = ssh_credentials.get_credentials(host, user)
    cmd = credentials.get_ssh_cmd_prefix() + ' -o LogLevel=QUIET -t "' + cmd + '"'
    if output:
        return shell.call_and_get_output(cmd, shell=True)
    else:
        shell.call(cmd, shell=True, wait=True)


def open(filepath, mode='r', credentials=None, **kwargs):
    user, host, path = _parse_filename(filepath)
    return SSHFile(path, user, host, mode=mode)


def mkdir(path, mode=0o777):
    user, host, path = _parse_filename(path)
    _run_ssh_cmd(user, host, 'mkdir '+path)


def rmdir(path):
    user, host, path = _parse_filename(path)
    _run_ssh_cmd(user, host, 'rmdir '+path)


def makedirs(path, mode=0o777, exist_ok=False):
    raise ValueError()


def listdir(path='.'):
    user, host, path = _parse_filename(path)
    output = _run_ssh_cmd(user, host, 'ls '+path, output=True)
    output = output.strip().split()
    return output


def remove(path):
    raise ValueError()


def exists(path):
    user, host, path = _parse_filename(path)
    output = _run_ssh_cmd(user, host, 'ls '+path + ';exit 0', output=True)
    output = output.strip()
    if output:
        if output.endswith(b'No such file or directory'):
            return False
        return True
    return False


def isfile(path):
    raise ValueError()


def isdir(path):
    raise ValueError()
