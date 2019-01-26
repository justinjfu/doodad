import unittest

from doodad.credentials import ssh

class TestSSHCreds(unittest.TestCase):
    def test_user_host(self):
        creds = ssh.get_credentials(username='a', hostname='b.com')
        self.assertEqual(creds.user_host, 'a@b.com')

    def test_global_set(self):
        ssh.set_identity_file('mykey')
        creds = ssh.get_credentials(username='a', hostname='b.com')
        self.assertEqual(creds.identity_file, 'mykey')
