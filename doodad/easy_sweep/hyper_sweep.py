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
import os
import itertools
import multiprocessing
import random
from datetime import datetime

import doodad
from doodad.utils import REPO_DIR
import hashlib


class Sweeper(object):
    def __init__(self, hyper_config, repeat, include_name=False):
        self.hyper_config = hyper_config
        self.repeat = repeat
        self.include_name=include_name

    def __iter__(self):
        count = 0
        for _ in range(self.repeat):
            for config in itertools.product(*[val for val in self.hyper_config.values()]):
                kwargs = {key:config[i] for i, key in enumerate(self.hyper_config.keys())}
                if self.include_name:
                    timestamp = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
                    kwargs['exp_name'] = "%s_%d" % (timestamp, count)
                count += 1
                yield kwargs


def chunker(sweeper, num_chunks=10):
    import random
    import math
    chunks = [ [] for _ in range(num_chunks) ]
    print('computing chunks')
    configs = [config for config in sweeper]
    random.shuffle(configs)
    for i, config in enumerate(configs):
        chunks[i % num_chunks].append(config)
    #for config in sweeper:
    #    hash_ = int(hashlib.md5(repr(config).encode('utf-8')).hexdigest(), 16)
    #    task_chunk = hash_ % num_chunks
    #    chunks[task_chunk].append(config)
    print('num chunks:  ', num_chunks)
    print('chunk sizes: ', [len(chunk) for chunk in chunks])
    print('total jobs:  ', sum([len(chunk) for chunk in chunks]))
    print('continue?(y/n)')
    resp = str(input())
    if resp == 'y':
        return chunks
    else:
        return []


def run_sweep_serial(run_method, params, repeat=1):
    sweeper = Sweeper(params, repeat)
    for config in sweeper:
        run_method(**config)


def kwargs_wrapper(args_method):
    args, method = args_method
    return method(**args)


def run_sweep_parallel(run_method, params, repeat=1, num_cpu=multiprocessing.cpu_count()):
    sweeper = Sweeper(params, repeat)
    pool = multiprocessing.Pool(num_cpu)
    exp_args = []
    for config in sweeper:
        exp_args.append((config, run_method))
    random.shuffle(exp_args)
    pool.map(kwargs_wrapper, exp_args)


SCRIPTS_DIR = os.path.join(REPO_DIR, 'scripts')
def run_sweep_doodad(run_method, params, run_mode, mounts, repeat=1, test_one=False, args=None, python_cmd='python'):
    if args is None:
        args = {}
    sweeper = Sweeper(params, repeat)
    for config in sweeper:
        def run_method_args():
            run_method(**config)
        args['run_method'] = run_method_args
        doodad.launch_python(
                target = os.path.join(SCRIPTS_DIR, 'run_experiment_lite_doodad.py'),
                mode=run_mode,
                mount_points=mounts,
                use_cloudpickle=True,
                python_cmd=python_cmd,
                args=args,
        )
        if test_one:
            break


def run_sweep_doodad_chunked(run_method, params, run_mode, mounts, repeat=1, test_one=False, args=None, python_cmd='python',
        num_chunks=10):
    if args is None:
        args = {}
    sweeper = Sweeper(params, repeat)

    for configs in chunker(sweeper, num_chunks=num_chunks):
        def run_method_args():
            for config in configs:
                run_method(**config)
        args['run_method'] = run_method_args
        doodad.launch_python(
                target = os.path.join(SCRIPTS_DIR, 'run_experiment_lite_doodad.py'),
                mode=run_mode,
                mount_points=mounts,
                use_cloudpickle=True,
                python_cmd=python_cmd,
                args=args,
        )
        if test_one:
            break


def run_single_doodad(run_method, kwargs, run_mode, mounts, repeat=1, args=None, python_cmd='python'):
    """ Run a single function via doodad """
    if args is None:
        args = {}
    def run_method_args():
        run_method(**kwargs)
    args['run_method'] = run_method_args
    doodad.launch_python(
            target = os.path.join(SCRIPTS_DIR, 'run_experiment_lite_doodad.py'),
            mode=run_mode,
            mount_points=mounts,
            use_cloudpickle=True,
            python_cmd=python_cmd,
            args=args,
    )


if __name__ == "__main__":
    def example_run_method(exp_name, param1, param2='a', param3=3, param4=4):
        import time
        time.sleep(1.0)
        print(exp_name, param1, param2, param3, param4)
    sweep_op = {
        'param1': [1e-3, 1e-2, 1e-1],
        'param2': [1,5,10,20],
        'param3': [True, False]
    }
    run_sweep_parallel(example_run_method, sweep_op, repeat=2)
