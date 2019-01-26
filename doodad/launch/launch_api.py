import os

from doodad.darchive import archive_builder_docker as archive_builder
from doodad.darchive import mount


def run_command(
    command,
    mode,
    mounts=tuple(),
    return_output=False,
    ):

    archive = archive_builder.build_archive(payload_script=command,
                                            verbose=False, 
                                            docker_image='python:3',
                                            mounts=mounts)
    result = mode.run_script(archive, return_output=return_output)
    if return_output:
        result = archive_builder._strip_stdout(result)
    return result


def run_python(
        target,
        mode,
        target_mount_dir='target',
        mounts=tuple(),
        return_output=False,
    ):
    target_dir = os.path.dirname(target)
    target_mount_dir = os.path.join(target_mount_dir, os.path.basename(target_dir))
    target_mount = mount.MountLocal(local_dir=target_dir, mount_point=target_mount_dir)
    mounts = list(mounts) + [target_mount]
    target_full_path = os.path.join(target_mount.mount_point, os.path.basename(target))
    command = make_python_command(
        target_full_path,
    )

    archive = archive_builder.build_archive(payload_script=command,
                                            verbose=False, 
                                            docker_image='python:3',
                                            mounts=mounts)
    result = mode.run_script(archive, return_output=return_output)
    if return_output:
        result = archive_builder._strip_stdout(result)
    return result


def make_python_command(
        target,
        python_cmd='python',
):
    cmd = '%s %s' % (python_cmd, target)
    return cmd
