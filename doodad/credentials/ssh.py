import os

SSH_IDENTITY_FILE = None

class SSHCredentials(object):
    """
    Container for SSH credentials

    Args:
        hostname (str):
        username (str):
        identity_file (str, optional):
            Path to a private key file for SSL public key authentication
    """
    def __init__(self, hostname, username, identity_file=None):
        self.hostname = hostname
        self.username = username
        if identity_file:
            self.identity_file = os.path.expanduser(identity_file)
        else:
            self.identity_file = None

    def get_ssh_cmd_prefix(self):
        """
        Return a command prefix
            Ex.
            'ssh user@host -i id_file '
        """
        cmd = 'ssh %s@%s' % (self.username, self.hostname)
        if self.identity_file:
            cmd += ' -i %s' % self.identity_file
        return cmd + ' '

    def get_ssh_bash_cmd(self, cmd):
        prefix = self.get_ssh_cmd_prefix()
        return prefix + " '%s'"%cmd

    def get_ssh_script_cmd(self, script_name, shell_interpreter='bash'):
        # The following does not work with archive scripts
        # cmd = self.get_ssh_cmd_prefix()
        # cmd += "'%s -s' < %s" % (shell_interpreter, script_name)
        cmd = "{scp_cmd};" + \
              "{ssh_cmd}'{shell_interpreter} ./tmp_script.sh';" + \
              "{ssh_cmd}'rm ./tmp_script.sh'" 
        cmd = cmd.format(
            scp_cmd=self.get_scp_cmd(script_name, './tmp_script.sh', src_remote=False),
            ssh_cmd=self.get_ssh_cmd_prefix(),
            shell_interpreter=shell_interpreter
        )
        return cmd

    def get_scp_cmd(self, source, destination, src_remote=True, recursive=True):
        cmd = 'scp'
        if recursive:
            cmd += ' -r'
        if self.identity_file:
            cmd += ' -i %s' % self.identity_file
        if src_remote:
            cmd += ' %s@%s:%s' % (self.username, self.hostname, source)
            cmd += ' %s' % destination
        else:
            cmd += ' %s' % source
            cmd += ' %s@%s:%s' % (self.username, self.hostname, destination)
        return cmd

    @property
    def user_host(self):
        return '%s@%s' % (self.username, self.hostname)


def set_identity_file(id_file):
    """Set the identity file to be used for SSH connections."""
    global SSH_IDENTITY_FILE
    SSH_IDENTITY_FILE = id_file


def get_credentials(hostname, username):
    """Get SSH credentials and try to automatically 
    resolve the identity file via environment variable

    Returns:
        creds (SSHCredentials): A credentiasl object
    """
    if SSH_IDENTITY_FILE is not None:
        id_file = SSH_IDENTITY_FILE
    else:
        id_file = os.environ.get('DOODAD_SSH_IDENTITY', None)
    return SSHCredentials(hostname, username, identity_file=id_file)
