import os
import tempfile
import shutil
import time
import subprocess
import uuid

import doodad
from doodad.darchive import cmd_util

THIS_FILE_DIR = os.path.dirname(__file__)
MAKESELF_PATH = os.path.join(THIS_FILE_DIR, 'makeself.sh')
MAKESELF_HEADER_PATH = os.path.join(THIS_FILE_DIR, 'makeself-header.sh')
BEGIN_HEADER = '--- BEGIN DAR OUTPUT ---'

def build_archive(archive_filename=None, 
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
        for mount in mounts:
            mount.dar_build_archive(deps_dir)
        
        write_run_script(archive_dir, mounts, 
            payload_script=payload_script, verbose=verbose)  #TODO:depends on launch mode
        write_metadata(archive_dir)

        # create the self-extracting archive
        compile_archive(archive_dir, output_file)
    finally:
        shutil.rmtree(work_dir)
    return archive_filename

def write_metadata(arch_dir):
    with open(os.path.join(arch_dir, 'METADATA'), 'w') as f:
        f.write('doodad_version=%s\n' % doodad.__version__)
        f.write('unix_timestamp=%d\n' % time.time())
        f.write('uuid=%s\n' % uuid.uuid4())

def write_run_script(arch_dir, mounts, payload_script, verbose=False):
    runfile = os.path.join(arch_dir, 'run.sh')
    cmd_builder = cmd_util.CommandBuilder()
    cmd_builder.append('#!/bin/bash')
    cmd_builder.append('echo', 'Running Doodad Archive [DAR] $1')
    cmd_builder.append('echo', 'DAR build information:')
    cmd_builder.append('cat', './METADATA')
    for mount in mounts:
        cmd_builder.append('echo', 'Mounting %s' % mount)
        cmd_builder.append(mount.dar_extract_command())
    cmd_builder.append('echo', BEGIN_HEADER)
    cmd_builder.append(payload_script)

    with open(runfile, 'w') as f:
        f.write(cmd_builder.dump_script())

    if verbose:
        print('[VERBOSE] Run script:')
        with open(runfile) as f:
            print(f.read())
    os.chmod(runfile, 0o777)

def compile_archive(archive_dir, output_file):
    compile_cmd = "{mkspath} --header {mkhpath} {archive_dir} {output_file} {name} {run_script}"
    compile_cmd = compile_cmd.format(
        mkspath=MAKESELF_PATH,
        mkhpath=MAKESELF_HEADER_PATH,
        name='DAR',
        archive_dir=archive_dir,
        output_file=output_file,
        run_script='./run.sh'
    )
    subprocess.call(compile_cmd, shell=True)
    os.chmod(output_file, 0o777)

def run_archive(filename, encoding='utf-8', timeout=None):
    if '/' not in filename:
        filename = './'+filename
    p = subprocess.Popen([filename], stdout=subprocess.PIPE)
    output, errcode = p.communicate(timeout=timeout)
    output = output.decode(encoding)
    begin_output = output.find(BEGIN_HEADER, 0) + len(BEGIN_HEADER)
    output = output[begin_output+1:]
    # strip out 
    return output, errcode

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
  
