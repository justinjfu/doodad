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
            launcher.run_script(script_name)


class TestDockerMode(unittest.TestCase):
    def test_hello(self):
        launcher = mode.DockerMode(docker_image='ubuntu:18.04')
        with hello_script() as script_name:
            launcher.run_script(script_name)


if __name__ == '__main__':
    unittest.main()
