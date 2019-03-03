import unittest
import tempfile
import os
import os.path as path
import shutil

from doodad import mount
from doodad.darchive import archive_builder_docker
from doodad.utils import TESTING_DIR, TESTING_OUTPUT_DIR


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

    def test_git_repo_pythonpath(self):
        mnts = []
        mnts.append(mount.MountGit(
            git_url='https://github.com/justinjfu/doodad.git',
            branch='archive_builder_test',
            ssh_identity='~/.ssh/github',
            mount_point='./code/doodad',
            pythonpath=True
        ))

        payload_script = 'python3 ./code/doodad/test/test_import.py'
        archive = archive_builder_docker.build_archive(payload_script=payload_script,
                                                verbose=False, 
                                                docker_image='python:3',
                                                mounts=mnts)
        output, errors = archive_builder_docker.run_archive(archive, timeout=5)
        output = output.strip()
        self.assertEqual(output, 'apple')

    def test_local_repo(self):
        mnts = []
        mnts.append(mount.MountLocal(
            local_dir=TESTING_DIR,
            mount_point='./mymount',
            output=False
        ))
        payload_script = 'cat ./mymount/secret.txt'
        
        archive = archive_builder_docker.build_archive(payload_script=payload_script,
                                                verbose=False, 
                                                docker_image='python:3',
                                                mounts=mnts)
        output, errors = archive_builder_docker.run_archive(archive, timeout=5)
        output = output.strip()
        self.assertEqual(output, 'apple')

    def test_local_output(self):
        mnts = []
        try:
            shutil.rmtree(TESTING_OUTPUT_DIR)
        except OSError:
            pass
        temp_dir = TESTING_OUTPUT_DIR
        os.makedirs(TESTING_OUTPUT_DIR)
        mnts.append(mount.MountLocal(
            local_dir=temp_dir,
            mount_point='/mymount',
            output=True
        ))
        payload_script = 'echo hello123 > /mymount/secret.txt'
        archive = archive_builder_docker.build_archive(payload_script=payload_script,
                                                verbose=False, 
                                                docker_image='python:3',
                                                mounts=mnts)
        archive_builder_docker.run_archive(archive, timeout=5, get_output=False)
        with open(path.join(temp_dir, 'secret.txt'), 'r') as f:
            output = f.read()
        self.assertEqual(output, 'hello123\n')

    def test_s3(self):
        """ Dry-run test for MountS3
        This test doesn't actually run things it just makes sure nothing errors.
        (we don't actually want to launch a test on EC2 and spend money) 
        """
        mnts = []
        mnts.append(mount.MountS3(
            s3_path='logs/mylogs',
            dry=True,
        ))
        payload_script = 'echo hello123'
        archive = archive_builder_docker.build_archive(payload_script=payload_script,
                                                verbose=False, 
                                                docker_image='python:3',
                                                mounts=mnts)

    def test_gcp(self):
        """ Dry-run test for MountGCP
        This test doesn't actually run things it just makes sure nothing errors.
        (we don't actually want to launch a test on EC2 and spend money) 
        """
        mnts = []
        mnts.append(mount.MountGCP(
            gcp_path='test_dir',
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

    def test_cli_args(self):
        payload_script = 'echo hi'
        archive = archive_builder_docker.build_archive(payload_script=payload_script,
                                                verbose=True, 
                                                docker_image='python:3')
        output, errors = archive_builder_docker.run_archive(archive, cli_args='--help', timeout=5)
        output = output.strip()
        self.assertEqual(output, 'hi --help')

if __name__ == '__main__':
    unittest.main()
