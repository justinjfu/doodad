import unittest
import os.path as path
import tempfile
import contextlib

from doodad.launch import mode
from doodad.utils import TESTING_DIR
from doodad.credentials import ssh


class TestLocal(unittest.TestCase):
    def test_mode(self):
        launcher = mode.LocalMode(shell_interpreter='bashy')
        self.assertEqual(
            launcher._get_run_command('myscript.sh'),
            'bashy myscript.sh'
        )


class TestSSH(unittest.TestCase):
    def test_mode(self):
        credentials = ssh.SSHCredentials(hostname='b.com', username='a')
        launcher = mode.SSHMode(credentials, shell_interpreter='bashy')
        self.assertEqual(
            launcher._get_run_command('myscript.sh'),
            'ssh a@b.com \'bashy -s\' < myscript.sh'
        )
