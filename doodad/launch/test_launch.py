import unittest
import os.path as path
import tempfile
import contextlib

from doodad import mode, mount
from doodad.launch import launch_api
from doodad.utils import TESTING_DIR


@contextlib.contextmanager
def hello_script(message='hello123'):
    with tempfile.NamedTemporaryFile('w+') as tfile:
        tfile.write('echo %s\n' % message)
        tfile.seek(0)
        yield tfile.name


class TestModes(unittest.TestCase):
    def test_local(self):
        launcher = mode.LocalMode()
        with hello_script() as script_name:
            output = launcher.run_script(script_name, return_output=True)
            self.assertEqual(output, 'hello123\n')
            output = launcher.run_script(script_name, return_output=True, dry=True)

    def test_gcp(self):
        # Run a dry test
        # (we don't actually want to spend money running GCP)
        launcher = mode.GCPMode(
            gcp_project='testing',
            gcp_bucket='testbucket',
            gcp_log_path='test_path',
            zone='us-east1-b',
        )
        with hello_script() as script_name:
            metadata = launcher.run_script(script_name, dry=True)
        self.assertEqual(metadata['gcp_bucket_path'], 'test_path')
        self.assertEqual(metadata['bucket_name'], 'testbucket')


class TestLaunchAPI(unittest.TestCase):
    def test_run_no_output(self):
        """Simple test to check for no errors
        """
        launcher = mode.LocalMode()
        result = launch_api.run_command(
            'echo hello123',
            mode=launcher,
            return_output=False
        )

    def test_run_command(self):
        launcher = mode.LocalMode()
        result = launch_api.run_command(
            'echo hello123',
            mode=launcher,
            return_output=True
        )
        self.assertEqual(result.strip(), 'hello123')

    def test_run_command_cli_args(self):
        launcher = mode.LocalMode()
        result = launch_api.run_command(
            'echo',
            cli_args='--help',
            mode=launcher,
            return_output=True
        )
        self.assertEqual(result.strip(), '--help')

    def test_run_python(self):
        launcher = mode.LocalMode()
        result = launch_api.run_python(
            target=path.join(TESTING_DIR, 'hello_world.py'),
            mode=launcher,
            return_output=True,
            docker_image='python:3'
        )
        print(result)
        self.assertEqual(result.strip(), 'hello123')


if __name__ == '__main__':
    unittest.main()
