import unittest

from doodad.dfile import doodad_file as dfile
from doodad.dfile import s3_file
from doodad.dfile import ssh_file
from doodad.dfile import http_file

class TestDFileOpen(unittest.TestCase):

    def test_s3(self):
        with dfile.open(r's3://test.bucket/test_file.txt', mode='w') as f:
            self.assertIsInstance(f, s3_file.S3File)

    def test_ssh(self):
        with dfile.open(r'ssh://user@hostname.org:~/test_file.txt', mode='w') as f:
            self.assertIsInstance(f, ssh_file.SSHFile)
            self.assertEqual(f.username, 'user')
            self.assertEqual(f.hostname, 'hostname.org')

    def test_http(self):
        with dfile.open(r'https://www.google.com', mode='r') as f:
            self.assertIsInstance(f, http_file.HTTPFile)

if __name__ == '__main__':
    unittest.main()
