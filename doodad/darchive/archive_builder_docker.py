import os
import sys
import tempfile
import shutil
import time
import subprocess
import uuid


import doodad
from doodad.darchive import cmd_util, mount

THIS_FILE_DIR = os.path.dirname(__file__)
MAKESELF_PATH = os.path.join(THIS_FILE_DIR, 'makeself.sh')
MAKESELF_HEADER_PATH = os.path.join(THIS_FILE_DIR, 'makeself-header.sh')
BEGIN_HEADER = '--- BEGIN DAR OUTPUT ---'

def build_archive(archive_filename=None, 
                  docker_image='ubuntu:18.04',
                  payload_script='',
                  launch_mode=None,
                  mounts=(),
                  verbose=False):
    if archive_filename is None:
        archive_filename = 'runfile.dar'

    # create a temporary work directory
    try:
        work_dir = tempfile.mkdtemp()
        archive_dir = os.path.join(work_dir, 'archive')
        os.makedirs(archive_dir)

        deps_dir = os.path.join(archive_dir, 'deps')
        os.makedirs(deps_dir)
        for mnt in mounts:
            mnt.dar_build_archive(deps_dir)
        
        write_run_script(archive_dir, mounts, 
            payload_script=payload_script, verbose=verbose)  #TODO:depends on launch mode
        write_docker_hook(archive_dir, docker_image, mounts, verbose=verbose)
        write_metadata(archive_dir)

        # create the self-extracting archive
        compile_archive(archive_dir, archive_filename, verbose=verbose)
    finally:
        shutil.rmtree(work_dir)
    return archive_filename

def write_metadata(arch_dir):
    with open(os.path.join(arch_dir, 'METADATA'), 'w') as f:
        f.write('doodad_version=%s\n' % doodad.__version__)
        f.write('unix_timestamp=%d\n' % time.time())
        f.write('uuid=%s\n' % uuid.uuid4())

def write_docker_hook(arch_dir, image_name, mounts, verbose=False):
    docker_hook_file = os.path.join(arch_dir, 'docker.sh')
    cmd_builder = cmd_util.CommandBuilder()
    cmd_builder.append('#!/bin/bash')
    mnt_cmd = ''.join([' -v %s:%s' % (mnt.local_dir, mnt.mount_point) 
        for mnt in mounts if isinstance(mnt, mount.MountLocal) and mnt.writeable])
    # mount the script into the docker image
    mnt_cmd += ' -v $(pwd):/payload'
    cmd_builder.append('docker run -i {mount_cmds} --user $UID {img} /bin/bash -c "cd /payload;./run.sh"'.format(
        img=image_name,
        mount_cmds=mnt_cmd,
    ))
    with open(docker_hook_file, 'w') as f:
        f.write(cmd_builder.dump_script())
    if verbose:
        print('[VERBOSE] Docker script:')
        with open(docker_hook_file) as f:
            print(f.read())
    os.chmod(docker_hook_file, 0o777)

def write_run_script(arch_dir, mounts, payload_script, verbose=False):
    runfile = os.path.join(arch_dir, 'run.sh')
    cmd_builder = cmd_util.CommandBuilder()
    cmd_builder.append('#!/bin/bash')
    if verbose:
        cmd_builder.echo('Running Doodad Archive [DAR] $1')
        cmd_builder.echo('DAR build information:')
        cmd_builder.append('cat', './METADATA')

    for mount in mounts:
        if verbose:
            cmd_builder.append('echo', 'Mounting %s' % mount)
        cmd_builder.append(mount.dar_extract_command())
    if verbose:
        cmd_builder.append('echo', BEGIN_HEADER)
    cmd_builder.append(payload_script)

    with open(runfile, 'w') as f:
        f.write(cmd_builder.dump_script())

    if verbose:
        print('[VERBOSE] Run script:')
        with open(runfile) as f:
            print(f.read())
    os.chmod(runfile, 0o777)

def compile_archive(archive_dir, output_file, verbose=False):
    compile_cmd = "{mkspath} --nocrc --nomd5 --header {mkhpath} {archive_dir} {output_file} {name} {run_script}"
    compile_cmd = compile_cmd.format(
        mkspath=MAKESELF_PATH,
        mkhpath=MAKESELF_HEADER_PATH,
        name='DAR',
        archive_dir=archive_dir,
        output_file=output_file,
        run_script='./docker.sh'
    )
    if verbose:
        pipe = sys.stdout
    else:
        pipe = subprocess.PIPE
    p = subprocess.Popen(compile_cmd, shell=True, stdout=pipe, stderr=pipe)
    p.wait()
    os.chmod(output_file, 0o777)

def run_archive(filename, encoding='utf-8', shell_interpreter='sh', timeout=None):
    if '/' not in filename:
        filename = './'+filename
    p = subprocess.Popen([shell_interpreter, filename, '--quiet'], stdout=subprocess.PIPE)
    output, errcode = p.communicate()
    output = _strip_stdout(output.decode(encoding))
    # strip out 
    return output, errcode


def _strip_stdout(output):
    begin_output = output.find(BEGIN_HEADER, 0) 
    if begin_output >= 0:
        begin_output += len(BEGIN_HEADER)
    output = output[begin_output+1:]
    return output

if __name__ == "__main__":
    import doodad.darchive.mount
    mnts = []
    mnts.append(doodad.launcher.mount.MountLocal(local_dir='./',
                                                mount_point='./code/doodad2'))
    mnts.append(doodad.launcher.mount.MountGit(
        git_url='git@github.com:justinjfu/doodad.git',
        branch='v2',
        mount_point='./code/doodad'
    ))

    payload_script = cmd_util.CommandBuilder()
    payload_script.append('python', './code/doodad/scripts/pull_s3_logs.py')
    
    build_archive('runfile.dar', 
        payload_script=payload_script,
        verbose=True, mounts=mnts)
  
