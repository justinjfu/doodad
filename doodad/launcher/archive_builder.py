import os
import tempfile
import shutil
import time
import subprocess

import doodad

THIS_FILE_DIR = os.path.dirname(__file__)
MAKESELF_PATH = os.path.join(THIS_FILE_DIR, 'makeself.sh')
MAKESELF_HEADER_PATH = os.path.join(THIS_FILE_DIR, 'makeself-header.sh')

def build_archive(output_file, 
                  launch_mode=None,
                  mounts=(),
                  verbose=False):
    # create a temporary work directory
    try:
        work_dir = tempfile.mkdtemp()
        archive_dir = os.path.join(work_dir, 'archive')
        os.makedirs(archive_dir)

        deps_dir = os.path.join(archive_dir, 'deps')
        os.makedirs(deps_dir)
        for mount in mounts:
            mount.dar_build_archive(deps_dir)
        
        write_run_script(archive_dir, mounts, verbose=verbose)  #TODO:depends on launch mode
        write_metadata(archive_dir)

        # create the self-extracting archive
        compile_archive(archive_dir, output_file)
    finally:
        shutil.rmtree(work_dir)

def write_metadata(arch_dir):
    with open(os.path.join(arch_dir, 'METADATA'), 'w') as f:
        f.write('doodad_version=%s\n' % doodad.__version__)
        f.write('unix_timestamp=%d\n' % time.time())

def write_run_script(arch_dir, mounts, verbose=False):
    runfile = os.path.join(arch_dir, 'run.sh')
    with open(runfile, 'w') as f:
        f.write('#!/bin/bash\n')
        f.write('echo Running Doodad Archive [DAR] $1\n')
        f.write('echo DAR build information:\n')
        f.write('cat ./METADATA\n')
        # set up docker?
        for mount in mounts:
            f.write('echo Mounting %s\n' % mount)
            f.write(mount.dar_extract_command()+'\n')

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

if __name__ == "__main__":
    import doodad.launcher.mount
    mnts = []
    mnts.append(doodad.launcher.mount.MountLocal(local_dir='./doodad'))
    mnts.append(doodad.launcher.mount.MountGit(
        git_url='git@github.com:justinjfu/doodad.git',
        branch='v2',
        mount_point='./doodad'
    ))
    
    build_archive('runfile.dar', verbose=True, mounts=mnts)
  