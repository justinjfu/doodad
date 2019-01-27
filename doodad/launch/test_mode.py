import unittest
import os.path as path
import tempfile
import contextlib

from doodad.launch import mode
from doodad.utils import TESTING_DIR
from doodad.credentials import ssh, ec2


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


class TestEC2(unittest.TestCase):
    def test_dry(self):
        credentials = ec2.AWSCredentials(aws_key='123', aws_secret='abc')
        launcher = mode.EC2Mode(
            ec2_credentials=credentials,
            s3_bucket='test.bucket',
            s3_log_path='test_log_path'
        )
        launcher.run_script('test_script.sh', dry=True)

