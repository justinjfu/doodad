"""
A simplified API for invoking commands via doodad.

Here is a simple hello world example using run_command:

result = launch_api.run_command(
    command='echo helloworld',
    mode=mode.LocalMode(),
)
"""
import os

from doodad.darchive import archive_builder_docker as archive_builder
from doodad import mount
from doodad import mode as launch_mode


def run_command(
        command,
        cli_args=None,
        mode=launch_mode.LocalMode(),
        mounts=tuple(),
        return_output=False,
        verbose=False,
        docker_image='ubuntu:18.04'
    ):
    """
    Runs a shell command using doodad via a specified launch mode.

    Args:
        command (str): A shell command
        cli_args (str): Command line args to pass
        mode (LaunchMode): A LaunchMode object
        mounts (tuple): A list/tuple of Mount objects
        return_output (bool): If True, returns stdout as a string.
            Do not use if the output will be large.
    
    Returns:
        A string output if return_output is True,
        else None
    """
    with archive_builder.temp_archive_file() as archive_file:
        archive = archive_builder.build_archive(archive_filename=archive_file,
                                                payload_script=command,
                                                verbose=False, 
                                                docker_image=docker_image,
                                                mounts=mounts)
        cmd = archive
        if cli_args:
            cmd = archive + ' -- ' + cli_args
        result = mode.run_script(cmd, return_output=return_output, verbose=verbose)
    if return_output:
        result = archive_builder._strip_stdout(result)

    return result


def run_python(
        target,
        target_mount_dir='target',
        mounts=tuple(),
        docker_image='python:3',
        **kwargs
    ):
    """
    Runs a python script using doodad via a specified launch mode.

    Args:
        target (str): Path to a python script. i.e. '/home/user/hello.py'
        target_mount_dir (str): Directory to mount the target inside container.
            Default is 'target'. Changing this is usually unnecessary.
        mounts (tuple): A list/tuple of Mount objects
        **kwargs: Arguments to run_command

    Returns:
        A string output if return_output is True,
        else None
    """
    target_dir = os.path.dirname(target)
    target_mount_dir = os.path.join(target_mount_dir, os.path.basename(target_dir))
    target_mount = mount.MountLocal(local_dir=target_dir, mount_point=target_mount_dir)
    mounts = list(mounts) + [target_mount]
    target_full_path = os.path.join(target_mount.mount_point, os.path.basename(target))
    command = make_python_command(
        target_full_path,
    )
    return run_command(command, docker_image=docker_image, mounts=mounts, **kwargs)


def make_python_command(
        target,
        python_cmd='python',
    ):
    cmd = '%s %s' % (python_cmd, target)
    return cmd

