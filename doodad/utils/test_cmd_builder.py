import unittest
import sys

from doodad.utils import cmd_builder


class TestCmdBuilder(unittest.TestCase):
    def test_args(self):
        builder = cmd_builder.CommandBuilder()
        builder.append('cat', '12', '34')
        self.assertEqual(str(builder), 'cat 12 34')

    def test_recursive(self):
        builder1 = cmd_builder.CommandBuilder()
        builder2 = cmd_builder.CommandBuilder()

        builder1.append('a')
        builder1.append(builder2)
        builder1.append('c')
        builder2.append('b')

        self.assertEqual(str(builder1), 'a;b;c')
        self.assertEqual(str(builder2), 'b')

    def test_dump(self):
        builder = cmd_builder.CommandBuilder()
        builder.append('a')
        builder.append('b')
        builder.append('c')
        self.assertEqual(builder.dump_script(), 'a\nb\nc')
