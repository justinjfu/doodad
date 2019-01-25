import unittest
import os.path as path
import tempfile
import contextlib

from doodad.launch import mode
from doodad.launch import launch_api


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


class TestLaunchAPI(unittest.TestCase):
    def test_hello(self):
        launcher = mode.LocalMode()
        result = launch_api.run_command(
            'echo hello123',
            mode=launcher,
            return_output=True
        )
        self.assertEqual(result, 'hello123\n')


if __name__ == '__main__':
    unittest.main()
