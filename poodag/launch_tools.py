import os

from .mode import LOCAL
from .arg_parse import encode_args, ARGS_DATA
from .mount import MountLocal


def launch_shell(
    command,
    mode=LOCAL,
    dry=False,
    mount_points=None,
    ):
    if mount_points is None:
        mount_points = []
    mode.launch_command(command, dry=dry)


def launch_python(
    target,
    python_cmd='python',
    mode=LOCAL,
    mount_points=None,
    args=None,
    env=None,
    dry=False,
    ):
    target_full_path = os.path.realpath(target)
    if args is None:
        args = {}
    if mount_points is None:
        mount_points = []

    # mount
    target_dir = os.path.dirname(target)
    mount_points.append(MountLocal(local_dir=target_dir, mount_point=target_dir))

    command = make_python_command(target_full_path, args=args, python_cmd=python_cmd)
    mode.launch_command(command, mount_points=mount_points, dry=dry)


def make_python_command(target, python_cmd='python', args=None):
    cmd = '%s %s' % (python_cmd, target)

    args_encoded = encode_args(args)
    if args:
        cmd += ' --%s "%s"' % (ARGS_DATA, args_encoded)
    return cmd

