import unittest
import os.path as path

from doodad.dfile import doodad_file as dfile
from doodad.dfile import s3_file
from doodad.dfile import ssh_file
from doodad.dfile import http_file

from doodad.darchive import mount, archive_builder_docker
from doodad.utils import TESTING_DIR


class TestDockerArchiveBuilder(unittest.TestCase):
    def test_git_repo(self):
        mnts = []
        mnts.append(mount.MountGit(
            git_url='https://github.com/justinjfu/doodad.git',
            branch='archive_builder_test',
            ssh_identity='~/.ssh/github',
            mount_point='./code/doodad'
        ))

        payload_script = 'python3 ./code/doodad/test/hello_world.py'
        
        archive = archive_builder_docker.build_archive(payload_script=payload_script,
                                                verbose=False, 
                                                docker_image='python:3',
                                                mounts=mnts)
        output, errors = archive_builder_docker.run_archive(archive, timeout=5)
        output = output.strip()
        self.assertEqual(output, 'hello world!')

    def test_local_repo(self):
        mnts = []
        mnts.append(mount.MountLocal(
            local_dir=TESTING_DIR,
            mount_point='./mymount'
        ))
        payload_script = 'cat ./mymount/secret.txt'
        
        archive = archive_builder_docker.build_archive(payload_script=payload_script,
                                                verbose=False, 
                                                docker_image='python:3',
                                                mounts=mnts)
        output, errors = archive_builder_docker.run_archive(archive, timeout=5)
        output = output.strip()
        self.assertEqual(output, 'apple')

    def test_s3(self):
        """ This test doesn't actually run things it just makes sure nothing errors.
        (we don't actually want to launch a test on EC2 and spend money) 
        """
        mnts = []
        mnts.append(mount.MountS3(
            region='us-west1',
            s3_bucket='my.bucket',
            s3_path='logs/mylogs',
            local_dir=TESTING_DIR,
            dry=True,
        ))
        payload_script = 'echo hello123'
        archive = archive_builder_docker.build_archive(payload_script=payload_script,
                                                verbose=False, 
                                                docker_image='python:3',
                                                mounts=mnts)

    def test_gcp(self):
        """ This test doesn't actually run things it just makes sure nothing errors.
        (we don't actually want to launch a test on EC2 and spend money) 
        """
        mnts = []
        mnts.append(mount.MountGCP(
            zone='us-west1',
            gcp_bucket='my.bucket',
            gcp_path='logs/mylogs',
            local_dir=TESTING_DIR,
            dry=True,
        ))
        payload_script = 'echo hello123'
        archive = archive_builder_docker.build_archive(payload_script=payload_script,
                                                verbose=False, 
                                                docker_image='python:3',
                                                mounts=mnts)

    def test_verbose(self):
        payload_script = 'echo hello123'
        archive = archive_builder_docker.build_archive(payload_script=payload_script,
                                                verbose=True, 
                                                docker_image='python:3')
        output, errors = archive_builder_docker.run_archive(archive, timeout=5)
        output = output.strip()
        self.assertEqual(output, 'hello123')

if __name__ == '__main__':
    unittest.main()
