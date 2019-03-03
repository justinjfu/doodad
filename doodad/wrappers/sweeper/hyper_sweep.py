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


class Sweeper(object):
    def __init__(self, hyper_config):
        self.hyper_config = hyper_config
        self.include_name=include_name

    def __iter__(self):
        count = 0
        for config in itertools.product(*[val for val in self.hyper_config.values()]):
            kwargs = {key:config[i] for i, key in enumerate(self.hyper_config.keys())}
            count += 1
            yield kwargs


def chunker(sweeper, num_chunks=10):
    chunks = [ [] for _ in range(num_chunks) ]
    print('computing chunks')
    configs = [config for config in sweeper]
    random.shuffle(configs)
    for i, config in enumerate(configs):
        chunks[i % num_chunks].append(config)
    print('num chunks:  ', num_chunks)
    print('chunk sizes: ', [len(chunk) for chunk in chunks])
    print('total jobs:  ', sum([len(chunk) for chunk in chunks]))
    print('continue?(y/n)')
    resp = str(input())
    if resp == 'y':
        return chunks
    else:
        return []


def run_sweep_doodad(target, params, run_mode, mounts, test_one=False, docker_image='python:3'):
    sweeper = Sweeper(params)
    for config in sweeper:
        #TODO(Justin): don't rebuild the archive each time.
        doodad.launch.run_python(
                target=target,
                mode=run_mode,
                docker_image=docker_image,
                mount_points=mounts,
                cli_args=' '.join(['--%s %s' % (key, config[key]) for key in config]),
        )
        if test_one:
            break


def run_sweep_doodad_chunked(target, params, run_mode, mounts, num_chunks=10, docker_image='python:3'):
    sweeper = Sweeper(params)
    chunks = chunker(sweeper, num_chunks)
    for chunk in chunks:
        command = ''
        for config in chunk:
            cli_args=' '.join(['--%s %s' % (key, config[key]) for key in config]),
            command += '%s %s;' % (target, cli_args)
        doodad.launch.run_command(
                command=command,
                mode=run_mode,
                docker_image=docker_image,
                mount_points=mounts,
        )


def run_single_doodad(target, kwargs, run_mode, mounts, docker_image='python:3'):
    """ Run a single function via doodad """
    doodad.launch_python(
            target = target,
            mode=run_mode,
            mount_points=mounts,
            python_cmd=python_cmd,
            cli_args=' '.join(['--%s %s' % (key, kwargs[key]) for key in kwargs]),
    )

