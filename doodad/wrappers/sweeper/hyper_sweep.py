"""
Usage

args = {
'param1': [1e-3, 1e-2, 1e-2],
'param2': [1,5,10,20],
}

run_sweep_parallel(func, args)

or

run_sweep_serial(func, args)

"""
import math
import os
import itertools
import multiprocessing
import random
from datetime import datetime
import hashlib
import doodad
from doodad import mount
from doodad.launch import launch_api
from doodad.darchive import archive_builder_docker as archive_builder


class Sweeper(object):
    def __init__(self, hyper_config):
        self.hyper_config = hyper_config

    def __iter__(self):
        count = 0
        for config in itertools.product(*[val for val in self.hyper_config.values()]):
            kwargs = {key:config[i] for i, key in enumerate(self.hyper_config.keys())}
            count += 1
            yield kwargs


def chunker(sweeper, num_chunks=10, confirm=True):
    chunks = [ [] for _ in range(num_chunks) ]
    print('computing chunks')
    configs = [config for config in sweeper]
    random.shuffle(configs, random.random)
    for i, config in enumerate(configs):
        chunks[i % num_chunks].append(config)
    print('num chunks:  ', num_chunks)
    print('chunk sizes: ', [len(chunk) for chunk in chunks])
    print('total jobs:  ', sum([len(chunk) for chunk in chunks]))

    resp = 'y'
    if confirm:
        print('continue?(y/n)')
        resp = str(input())

    if resp == 'y':
        return chunks
    else:
        return []


def run_sweep_doodad(target, params, run_mode, mounts, test_one=False, docker_image='python:3', return_output=False, verbose=False):

    # build archive
    target_dir = os.path.dirname(target)
    target_mount_dir = os.path.join('target', os.path.basename(target_dir))
    target_mount = mount.MountLocal(local_dir=target_dir, mount_point=target_mount_dir)
    mounts = list(mounts) + [target_mount]
    target_full_path = os.path.join(target_mount.mount_point, os.path.basename(target))
    command = launch_api.make_python_command(
        target_full_path
    )

    print('Launching jobs with mode %s' % run_mode)
    results = []
    njobs = 0
    with archive_builder.temp_archive_file() as archive_file:
        archive = archive_builder.build_archive(archive_filename=archive_file,
                                                payload_script=command,
                                                verbose=verbose,
                                                docker_image=docker_image,
                                                use_gpu_image=run_mode.use_gpu,
                                                mounts=mounts)

        sweeper = Sweeper(params)
        for config in sweeper:
            njobs += 1
            cli_args= ' '.join(['--%s %s' % (key, config[key]) for key in config])
            cmd = archive + ' -- ' + cli_args
            result = run_mode.run_script(cmd, return_output=return_output, verbose=False)
            if return_output:
                result = archive_builder._strip_stdout(result)
                results.append(result)
            if test_one:
                break
    print('Launching completed for %d jobs' % njobs)
    run_mode.print_launch_message()
    return tuple(results)


def run_sweep_doodad_chunked(target, params, run_mode, mounts, num_chunks=10, docker_image='python:3', return_output=False, test_one=False, confirm=True, verbose=False):
    # build archive
    target_dir = os.path.dirname(target)
    target_mount_dir = os.path.join('target', os.path.basename(target_dir))
    target_mount = mount.MountLocal(local_dir=target_dir, mount_point=target_mount_dir)
    mounts = list(mounts) + [target_mount]
    target_full_path = os.path.join(target_mount.mount_point, os.path.basename(target))
    command = launch_api.make_python_command(
        target_full_path
    )

    print('Launching jobs with mode %s' % run_mode)
    results = []
    njobs = 0
    with archive_builder.temp_archive_file() as archive_file:
        archive = archive_builder.build_archive(archive_filename=archive_file,
                                                payload_script=command,
                                                verbose=verbose,
                                                docker_image=docker_image,
                                                use_gpu_image=run_mode.use_gpu,
                                                mounts=mounts)

        sweeper = Sweeper(params)
        chunks = chunker(sweeper, num_chunks, confirm=confirm)
        for chunk in chunks:
            command = ''
            for config in chunk:
                njobs += 1
                cli_args=' '.join(['--%s %s' % (key, config[key]) for key in config])
                single_command = archive + ' -- ' + cli_args
                command += '%s;' % single_command

            result = run_mode.run_script(command, return_output=return_output, verbose=False)
            if return_output:
                result = archive_builder._strip_stdout(result)
                results.append(result)
            if test_one:
                break
    print('Launching completed for %d jobs on %d machines' % (njobs, num_chunks))
    run_mode.print_launch_message()
    return tuple(results)

