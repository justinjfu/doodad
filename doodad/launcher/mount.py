"""
These objects are pointers to code/data you wish to give access
to a launched job.

Each object defines a source and a mount point (where the directory will be visible
to the launched process)

"""
import os
import shutil
import tarfile
import tempfile
from contextlib import contextmanager


class Mount(object):
    """
    Args:
        mount_point (str): Location of directory visible to the running process
        pythonpath (bool): If True, adds this folder to the $PYTHON_PATH environment variable
        output (bool): If False, this is a "code" directory. If True, this should be an empty
            "output" directory (nothing will be copied to remote)
    """
    def __init__(self, mount_point=None, pythonpath=False, output=False):
        self.pythonpath = pythonpath
        self.read_only = not output
        self.mount_point = mount_point

    def dar_build_archive(self, deps_dir):
        raise NotImplementedError()

    def dar_extract_command(self):
        raise NotImplementedError()

class MountLocal(Mount):
    def __init__(self, local_dir, mount_point=None, cleanup=True,
                filter_ext=('.pyc', '.log', '.git', '.mp4'),
                filter_dir=('data',),
                **kwargs):
        super(MountLocal, self).__init__(mount_point=mount_point, **kwargs)
        self.local_dir = os.path.realpath(os.path.expanduser(local_dir))
        self.local_dir_raw = local_dir
        self.cleanup = cleanup
        self.filter_ext = filter_ext
        self.filter_dir = filter_dir
        if mount_point is None:
            self.mount_point = mount_point
            self.no_remount = True
        else:
            self.no_remount = False
        #print('local_dir %s, mount_point %s(%s)' % (self.local_dir, self.mount_point, mount_point))

    def create_if_nonexistent(self):
        os.makedirs(self.local_dir, exist_ok=True)

    @contextmanager
    def gzip(self):
        """
        Return filepath to a gzipped version of this directory for uploading
        """
        assert self.read_only
        def filter_func(tar_info):
            filt = any([tar_info.name.endswith(ext) for ext in self.filter_ext]) or any([ tar_info.name.endswith('/'+ext) for ext in self.filter_dir])
            if filt:
                return None
            return tar_info
        with tempfile.NamedTemporaryFile('wb+', suffix='.tar') as tf:
            # make a tar.gzip archive of directory
            with tarfile.open(fileobj=tf, mode="w") as tar:
                #tar.add(self.local_dir, arcname=os.path.splitext(os.path.basename(tf.name))[0], filter=filter_func)
                tar.add(self.local_dir, arcname=os.path.basename(self.local_dir), filter=filter_func)
            tf.seek(0)
            yield tf.name

    def dar_build_archive(self, deps_dir):
        # make a symlink to deps dir
        dep_dir = os.path.join(deps_dir, 'local', self.local_dir.replace('/', '_'))
        os.makedirs(os.path.join(deps_dir, 'local'))
        #os.symlink(self.local_dir, dep_dir)
        shutil.copytree(self.local_dir, dep_dir)

    def dar_extract_command(self):
        # make a symlink to mount dir
        return 'ln -s ./deps/local/{dep_name} {mount}'.format(
            dep_name=self.local_dir.replace('/', '_'),
            mount=self.mount_point
        )

    def __str__(self):
        return 'MountLocal@%s'%self.local_dir

    def docker_mount_dir(self):
         return os.path.join('/mounts', self.mount_point.replace('~/',''))


class MountGitRepo(Mount):
    def __init__(self, git_url, branch=None,
                 git_credentials=None, **kwargs):
        super(MountGitRepo, self).__init__(read_only=True, **kwargs)
        self.git_url = git_url
        self.git_credentials = git_credentials
        raise NotImplementedError()


class MountS3(Mount):
    def __init__(self, s3_path, s3_bucket=None, sync_interval=15, output=False,
            include_types=('*.txt', '*.csv', '*.json', '*.gz', '*.tar', '*.log', '*.pkl'), **kwargs):
        super(MountS3, self).__init__(**kwargs)
        if s3_bucket is None:
            # load from config
            from doodad.ec2.autoconfig import AUTOCONFIG
            s3_bucket = AUTOCONFIG.s3_bucket()
        self.s3_bucket = s3_bucket
        self.s3_path = s3_path
        self.output = output
        self.sync_interval = sync_interval
        self.sync_on_terminate = True
        self.include_types = include_types

    def __str__(self):
        return 'MountS3@s3://%s/%s'% (self.s3_bucket, self.s3_path)

    @property
    def include_string(self):
        return ' '.join(['--include \'%s\''%type_ for type_ in self.include_types])

    def dar_build_archive(self, deps_dir):
        # first upload directory to S3
        # next, create the script to pull from S3
        dep_dir = os.path.join(deps_dir, 's3', name)
        os.makedirs(os.path.join(deps_dir, 's3'))
        raise NotImplementedError()

    def dar_extract_command(self):
        # execute the script to pull from S3
        raise NotImplementedError()
        return './deps/s3/{name}/extract.sh'.format(
            name=None,
        )