from doodad.darchive import archive_builder_docker as archive_builder

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