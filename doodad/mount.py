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

from doodad.apis import aws_util
from doodad import utils 


class Mount(object):
    """
    Args:
        mount_point (str): Location of directory visible to the running process *inside* container
        pythonpath (bool): If True, adds this folder to the $PYTHONPATH environment variable
        output (bool): If False, this is a "code" directory. If True, this should be an empty
            "output" directory (nothing will be copied to remote)
    """
    def __init__(self, mount_point=None, pythonpath=False, output=False):
        self.pythonpath = pythonpath
        self.read_only = not output
        self.mount_point = mount_point
        self._name = None
        self.local_dir = None

    def dar_build_archive(self, deps_dir):
        raise NotImplementedError()

    def dar_extract_command(self):
        raise NotImplementedError()

    @property
    def writeable(self):
        return not self.read_only

    @property
    def name(self):
        return self._name

    def __str__(self):
        return '%s@%s'% (type(self).__name__, self.name)


class MountLocal(Mount):
    """
    """
    def __init__(self, local_dir, mount_point=None, cleanup=True,
                filter_ext=('.pyc', '.log', '.git', '.mp4'),
                filter_dir=('data', '.git'),
                **kwargs):
        super(MountLocal, self).__init__(mount_point=mount_point, **kwargs)
        self.local_dir = os.path.realpath(os.path.expanduser(local_dir))
        self._name = self.local_dir.replace('/', '_')
        self.sync_dir = local_dir
        self.cleanup = cleanup
        self.filter_ext = filter_ext
        self.filter_dir = filter_dir
        if self.writeable:
            if not self.mount_point.startswith('/'):
                raise ValueError('Output mount points must be absolute')
        if mount_point is None:
            self.mount_point = self.local_dir
        else:
            assert not self.mount_point.endswith('/'), "Do not end mount points with backslash"

    def ignore_patterns(self, dirname, contents):
        to_ignore = []
        for content in contents:
            if any([content.endswith(ext) for ext in self.filter_ext]):
                to_ignore.append(content)
            elif any([content == _dirname for _dirname in self.filter_dir]):
                to_ignore.append(content)
        return to_ignore

    def dar_build_archive(self, deps_dir):
        utils.makedirs(os.path.join(deps_dir, 'local'))
        dep_dir = os.path.join(deps_dir, 'local', self.name)
        extract_file = os.path.join(dep_dir, 'extract.sh')
        mount_point = os.path.dirname(self.mount_point)

        if self.read_only:
            shutil.copytree(self.local_dir, dep_dir, ignore=self.ignore_patterns)
        else:
            os.makedirs(dep_dir)
        with open(extract_file, 'w') as f:
            if self.read_only:
                f.write('mkdir -p %s\n' % mount_point)
                f.write('mv ./deps/local/{name} {mount}\n'.format(name=self.name, mount=self.mount_point))
            else:
                f.write('mkdir -p %s\n' % mount_point)
            if self.pythonpath:
                f.write('export PYTHONPATH=$PYTHONPATH:{repo_dir}\n'.format(repo_dir=mount_point))
        os.chmod(extract_file, 0o777)

    def dar_extract_command(self):
        return './deps/local/{name}/extract.sh'.format(
            name=self.name,
        )

    def __str__(self):
        return 'MountLocal@%s'%self.local_dir

    def docker_mount_dir(self):
         return os.path.join('/mounts', self.mount_point.replace('~/',''))


class MountGit(Mount):
    def __init__(self, git_url, branch=None,
                 ssh_identity=None, **kwargs):
        super(MountGit, self).__init__(output=False, **kwargs)
        self.git_url = git_url
        self.repo_name = os.path.splitext(os.path.split(git_url)[1])[0]
        assert self.mount_point.endswith(self.repo_name)
        self.ssh_identity = ssh_identity
        if ssh_identity is not None:
            self.ssh_identity = os.path.expanduser(ssh_identity)
        self.branch = branch
        self._name = self.repo_name

    def dar_build_archive(self, deps_dir):
        dep_dir = os.path.join(deps_dir, 'git', self.name)
        os.makedirs(dep_dir)
        
        extract_file = os.path.join(dep_dir, 'extract.sh')
        with open(extract_file, 'w') as f:
            mount_point = os.path.dirname(self.mount_point)
            f.write('mkdir -p %s\n' % mount_point)
            f.write('pushd %s > /dev/null\n' % mount_point)
            if self.ssh_identity:
                shutil.copy(self.ssh_identity, dep_dir)
                id_file = os.path.split(self.ssh_identity)[1]
                id_file = os.path.join('/dar_payload/deps/git/{name}'.format(name=self.name), id_file)
                f.write("GIT_SSH_COMMAND='ssh -o StrictHostKeyChecking=no -i {id}' git clone --quiet {repo_url}\n".format(id=id_file, repo_url=self.git_url))
            else:
                f.write("git clone --quiet {repo_url}\n".format(repo_url=self.git_url))
            if self.branch:
                f.write('cd {repo_name}\n'.format(repo_name=self.repo_name))
                f.write('git checkout --quiet {branch}\n'.format(branch=self.branch))
            if self.pythonpath:
                f.write('export PYTHONPATH=$PYTHONPATH:{repo_dir}\n'.format(repo_dir=os.path.join(mount_point, self.repo_name)))
            f.write('popd > /dev/null\n')
        os.chmod(extract_file, 0o777)

    def dar_extract_command(self):
        return './deps/git/{name}/extract.sh'.format(
            name=self.name,
        )


class MountS3(Mount):
    def __init__(self, 
                s3_path, 
                sync_interval=15, 
                output=True,
                dry=False,
                include_types=('*.txt', '*.csv', '*.json', '*.gz', '*.tar', '*.log', '*.pkl'), 
                **kwargs):
        super(MountS3, self).__init__(output=output, **kwargs)
        # load from config
        if s3_path.startswith('/'):
            raise NotImplementedError('Local dir cannot be absolute')
        else:
            # We store everything into a fixed dir /doodad on the remote machine
            # so GCPMode knows to simply sync /doodad
            # (this is b/c we no longer pass in mounts to the launch mode)
            self.sync_dir = os.path.join('/doodad', s3_path)
        self.output = output
        self.sync_interval = sync_interval
        self.sync_on_terminate = True
        self.dry = dry
        self.include_types = include_types
        self._name = self.sync_dir.replace('/', '_')
        assert output

    def dar_build_archive(self, deps_dir):
        return 

    def dar_extract_command(self):
        return 'echo helloMountEC2'


class MountGCP(Mount):
    def __init__(self, 
                gcp_path=None,
                sync_interval=15, 
                output=True,
                dry=False,
                exclude_regex='*.tmp',
                **kwargs):
        """

        Args:
            zone (str): Zone name. i.e. 'us-west1-a'
            gcp_bucket (str): Bucket name
            gcp_path (str): Path underneath bucket. The full path will become
                gs://{gcp_bucket}/{gcp_path}
        """
        super(MountGCP, self).__init__(output=output, **kwargs)
        # load from config
        if gcp_path.startswith('/'):
            raise NotImplementedError('Local dir cannot be absolute')
        else:
            # We store everything into a fixed dir /doodad on the remote machine
            # so GCPMode knows to simply sync /doodad
            # (this is b/c we no longer pass in mounts to the launch mode)
            self.sync_dir = os.path.join('/doodad', gcp_path)
        self.output = output
        self.sync_interval = sync_interval
        self.sync_on_terminate = True
        self.exclude_string = '"'+exclude_regex+'"'
        self._name = self.sync_dir.replace('/', '_')
        self.dry = dry
        assert output

    def dar_build_archive(self, deps_dir):
        return 

    def dar_extract_command(self):
        return 'echo helloMountGCP'
