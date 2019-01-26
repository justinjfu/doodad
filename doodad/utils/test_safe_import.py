import unittest
import sys

from doodad.utils import safe_import


class TestSafeImport(unittest.TestCase):
    def test_good_import(self):
        lib = safe_import.try_import('sys')
        self.assertEqual(sys.copyright, lib.copyright)

    def test_bad_import(self):
        lib = safe_import.try_import('bad_library')
        with self.assertRaises(ImportError):
            lib.do_something()

    def test_bad_import_submodule(self):
        lib = safe_import.try_import('bad_library')
        lib.sublib = safe_import.try_import('bad_library.sblib')
        with self.assertRaises(ImportError):
            lib.sublib.do_something()
