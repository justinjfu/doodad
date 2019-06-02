import unittest
import contextlib
import itertools
import os
import random

from doodad import mode
from doodad.utils import TESTING_DIR
from doodad.wrappers.sweeper import hyper_sweep, launcher

SWEEPER_TEST_DIR = os.path.join(TESTING_DIR, 'wrappers', 'sweeper')
SWEEPER_TEST_FILE = os.path.join(SWEEPER_TEST_DIR, 'sweeper_script.py')

class TestSweeper(unittest.TestCase):
    def test_iter(self):
        cfg = {
            'arg1': [1,2],
            'arg2': ['a', 'b']
        }
        sweeper = hyper_sweep.Sweeper(cfg)
        cross_sweep = list(sweeper)
        self.assertEqual(len(cross_sweep), 4)
        self.assertIn({'arg1': 1, 'arg2': 'a'}, cross_sweep)
        self.assertIn({'arg1': 1, 'arg2': 'b'}, cross_sweep)
        self.assertIn({'arg1': 2, 'arg2': 'a'}, cross_sweep)
        self.assertIn({'arg1': 2, 'arg2': 'b'}, cross_sweep)


class TestDoodadSweep(unittest.TestCase):
    def setUp(self):
        self.sweeper = launcher.DoodadSweeper()

    def test_local_sweep(self):
        args = {
            'n': [1,3,5,7]
        }
        output = self.sweeper.run_sweep_local(
            target=SWEEPER_TEST_FILE,
            params=args,
            return_output=True
        )
        self.assertEqual(output, ('1\n', '3\n', '5\n', '7\n'))

    def test_local_chunked_sweep(self):
        args = {
            'n': [1,3,5,7]
        }
        random.seed(0)
        output = self.sweeper.run_sweep_local(
            target=SWEEPER_TEST_FILE,
            params=args,
            return_output=True,
            num_chunks=2,
            confirm=False,
        )
        self.assertEqual(output, ('5\n3\n', '1\n7\n'))
