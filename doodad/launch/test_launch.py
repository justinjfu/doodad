import unittest
import os.path as path
import tempfile
import contextlib

from doodad.launch import mode


@contextlib.contextmanager
def hello_script(message='hello123'):
    with tempfile.NamedTemporaryFile() as tfile:
        tfile.write('echo %s\n' % message)
        tfile.seek(0)
        yield tfile.name


class TestLocalMode(unittest.TestCase):
    def test_hello(self):
        launcher = mode.LocalMode()
        with hello_script() as script_name:
            output = launcher.run_script(script_name, return_output=True)
            self.assertEqual(output, 'hello123\n')


class TestDockerMode(unittest.TestCase):
    def setUp(self):
        self.img = 'ubuntu:18.04'
        self.launcher = mode.DockerMode(docker_image=self.img,
                                        docker_cmd='docker')

    def test_docker_cmd(self):
        launcher = mode.DockerMode(docker_image=self.img,
                                        docker_cmd='nvidia-docker')
        cmd = launcher._get_docker_cmd('foo')
        self.assertTrue(cmd.startswith('nvidia-docker run -i %s' % self.img))

    def test_hello(self):
        with hello_script() as script_name:
            output = self.launcher.run_script(script_name, return_output=True)
            self.assertEqual(output, 'hello123\n')


if __name__ == '__main__':
    unittest.main()
