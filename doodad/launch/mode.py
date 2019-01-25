from doodad.utils import shell

class LaunchMode(object):
    def __init__(self, shell_interpreter='sh', async_run=False):
        self.shell_interpreter = shell_interpreter
        self.async_run = async_run

    def run_script(self, script_filename, dry=False, return_output=False):
        """
        Runs a shell script.
        """
        if return_output:
            return shell.call_and_get_output(self.get_run_command(script_filename), shell=True, dry=dry)
        else:
            shell.call(self.get_run_command(script_filename), shell=True, dry=dry, wait=not self.async_run)

    def get_run_command(self, script_filename):
        raise NotImplementedError()


class LocalMode(LaunchMode):
    def __init__(self, **kwargs):
        super(LocalMode, self).__init__(**kwargs)

    def get_run_command(self, script_filename):
        return '%s %s' % (self.shell_interpreter, script_filename)


class SSHMode(LaunchMode):
    def __init__(self, ssh_credentials, **kwargs):
        super(SSHMode, self).__init__(**kwargs)
        self.ssh_cred = ssh_credentials

    def get_run_command(self, script_filename):
        return self.ssh_cred.get_ssh_script_cmd(script_filename)


class DockerMode(LaunchMode):
    def __init__(self, 
                 docker_image='scratch',
                 docker_cmd='docker',
                 **kwargs):
        super(DockerMode, self).__init__(**kwargs)
        self.docker_image = docker_image
        self.docker_cmd = docker_cmd

    def _get_docker_cmd(self, script):
        docker_cmd = '{docker_cmd} run -i {docker_img} /bin/{sh} -s < {script}'
        docker_cmd = docker_cmd.format(
            docker_cmd=self.docker_cmd,
            docker_img=self.docker_image,
            sh=self.shell_interpreter,
            script=script
        )
        return docker_cmd
    
    def get_run_command(self, script):
        return self._get_docker_cmd(script)
