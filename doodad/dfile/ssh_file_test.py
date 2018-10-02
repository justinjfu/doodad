import unittest
import os

from doodad.dfile import ssh_file
from doodad.credentials import ssh as ssh_credentials


class TestOS(unittest.TestCase):

    def setUp(self):
        ssh_credentials.set_identity_file(os.path.join('~/.ssh/rail_newton'))
        self.prefix = 'ssh://justinfu@newton4.banatao.berkeley.edu:'

    def test_mkdir(self):
        ssh_file.mkdir(self.prefix+'~/tmp_dir_test')

    def test_rmdir(self):
        ssh_file.rmdir(self.prefix+'~/tmp_dir_test')

    def test_lsdir(self):
        files = ssh_file.listdir(self.prefix + '~/')
        self.assertGreater(len(files), 0)

    def test_exists(self):
        exists = ssh_file.exists(self.prefix + '~/hi.txt')
        self.assertTrue(exists)
        exists = ssh_file.exists(self.prefix + '~/non_existent_file')
        self.assertFalse(exists)


if __name__ == '__main__':
    unittest.main()
