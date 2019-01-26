import unittest
import os.path as path

from doodad.dfile import doodad_file as dfile
from doodad.dfile import s3_file
from doodad.dfile import ssh_file
from doodad.dfile import http_file

from doodad.darchive import cmd_util, mount, archive_builder_docker
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

        payload_script = cmd_util.CommandBuilder()
        payload_script.append('python3', './code/doodad/test/hello_world.py')
        
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
        payload_script = cmd_util.CommandBuilder()
        payload_script.append('cat', './mymount/secret.txt')
        
        archive = archive_builder_docker.build_archive(payload_script=payload_script,
                                                verbose=False, 
                                                docker_image='python:3',
                                                mounts=mnts)
        output, errors = archive_builder_docker.run_archive(archive, timeout=5)
        output = output.strip()
        self.assertEqual(output, 'apple')

if __name__ == '__main__':
    unittest.main()
