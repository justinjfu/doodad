"""
These objects are pointers to code/data you wish to give access
to a launched job.

Each object defines a source and a mount point (where the directory will be visible
to the launched process)

"""
import os
import tarfile
import tempfile
from contextlib import contextmanager


class Mount(object):
    """
    Args:
        mount_point (str): Location of directory visible to the running process
        pythonpath (bool): If True, adds this folder to the $PYTHON_PATH environment variable
        read_only (bool): If True, this is a "code" directory. If False, this should be an empty 
            "output" directory (nothing will be copied to remote)
    """
    def __init__(self, mount_point=None, pythonpath=False, read_only=True):
        self.pythonpath = pythonpath
        self.read_only = read_only
        self.set_mount(mount_point)

    def set_mount(self, mount_point):
        if mount_point:
            self.mount_point = mount_point
        else:
            self.mount_point = mount_point


class MountLocal(Mount):
    def __init__(self, local_dir, mount_point=None, cleanup=True, **kwargs):
        super(MountLocal, self).__init__(mount_point=mount_point, **kwargs)
        self.local_dir = os.path.realpath(os.path.expanduser(local_dir))
        self.local_dir_raw = local_dir
        self.cleanup = cleanup
        if mount_point is None:
            self.set_mount(local_dir)
            self.no_remount = True
        else:
            self.no_remount = False
        #print('local_dir %s, mount_point %s(%s)' % (self.local_dir, self.mount_point, mount_point))
    
    def create_if_nonexistent(self):
        os.makedirs(self.local_dir, exist_ok=True)

    @contextmanager
    def gzip(self, filter_ext=('.pyc','.log', '.git')):
        """
        Return filepath to a gzipped version of this directory for uploading
        """
        assert self.read_only
        def filter_func(tar_info):
            filt = any([tar_info.name.endswith(ext) for ext in filter_ext])
            if filt:
                return None
            return tar_info
        with tempfile.NamedTemporaryFile('wb', suffix='.tar') as tf:
            # make a tar.gzip archive of directory
            with tarfile.open(fileobj=tf, mode="w") as tar:
                #tar.add(self.local_dir, arcname=os.path.splitext(os.path.basename(tf.name))[0], filter=filter_func)
                tar.add(self.local_dir, arcname=self.local_dir, filter=filter_func)
            yield tf.name

    def __str__(self):
        return 'MountLocal@%s'%self.local_dir


class MountGitRepo(Mount):
    def __init__(self, git_url, git_credentials=None, **kwargs):
        super(MountGitRepo, self).__init__(read_only=True, **kwargs)
        self.git_url = git_url
        self.git_credentials = git_credentials
        raise NotImplementedError()


class MountS3(Mount):
    def __init__(self, s3_bucket, s3_path, sync_interval=15, output=False, **kwargs):
        super(MountS3, self).__init__(**kwargs)
        self.s3_bucket = s3_bucket
        self.s3_path = s3_path
        self.output = output
        self.sync_interval = sync_interval
        self.sync_on_terminate = True

    def __str__(self):
        return 'MountS3@s3://%s/%s'% (self.s3_bucket, self.s3_path)
