import unittest

from doodad.dfile import doodad_file
from doodad.dfile import s3_file
from doodad.dfile import ssh_file

class TestDoodadFile(unittest.TestCase):

    def test_load_s3_file(self):
        f = doodad_file.open(r's3://test.bucket/test_file.txt', mode='w')
        self.assertIsInstance(f, s3_file.S3File)

    def test_load_ssh_file(self):
        f = doodad_file.open(r'user@hostname.org:~/test_file.txt', mode='w')
        self.assertIsInstance(f, ssh_file.SSHFile)
        self.assertEqual(f.username, 'user')
        self.assertEqual(f.hostname, 'hostname.org')

if __name__ == '__main__':
    unittest.main()
