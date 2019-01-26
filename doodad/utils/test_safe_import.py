import unittest
import sys

from doodad.utils import safe_import


class TestSafeImport(unittest.TestCase):
    def test_good_import(self):
        lib = safe_import.try_import('sys')
        self.assertEqual(sys.copyright, lib.copyright)

    def test_bad_import(self):
        lib = safe_import.try_import('nonexistent_library')
        with self.assertRaises(ImportError):
            lib.do_something()
