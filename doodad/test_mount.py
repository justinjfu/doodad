import unittest
import os
import os.path as path
import shutil
import tempfile
import contextlib

from doodad import mount
from doodad.utils import TESTING_DIR
from doodad.credentials import ssh, ec2


class TestLocal(unittest.TestCase):
    def test_filter(self):
        local_mount = mount.MountLocal('dummy', filter_ext=['.abc', '.xyz'], filter_dir=('foo',))
        to_ignore = local_mount.ignore_patterns('/data', ['a.abc', 'b.txt', 'foo', 'bar'])
        self.assertEqual({'a.abc', 'foo'}, set(to_ignore))

    def test_shutil_copy(self):
        source_dir = path.join(TESTING_DIR, 'mount_test', 'source_dir')
        target_dir = path.join(TESTING_DIR, 'mount_test', 'target_dir')
        local_mount = mount.MountLocal('dummy', filter_ext=['.pyc'], filter_dir=('foo',))
        try:
            shutil.copytree(source_dir, target_dir, ignore=local_mount.ignore_patterns)
            print('SOURCE_DIR:', os.listdir(source_dir))
            print('TARGET_DIR:', os.listdir(target_dir))
            self.assertEqual({'a.txt', 'bar'}, set(os.listdir(target_dir)))
        finally:
            shutil.rmtree(target_dir)


