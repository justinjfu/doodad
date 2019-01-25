from doodad.utils import shell

class LaunchMode(object):
    def __init__(self, shell_interpreter='sh'):
        self.shell_interpreter = shell_interpreter

    def run_script(self, script_filename):
        """
        Runs a shell script.
        """
        raise NotImplementedError()


class LocalMode(LaunchMode):
    def __init__(self, async_run=False, **kwargs):
        super(LocalMode, self).__init__(**kwargs)
        self.async_run = async_run

    def run_script(self, script_filename):
        # subprocess
        shell.call([self.shell_interpreter, script_filename], shell=False, wait=not self.async_run)


class SSHMode(LaunchMode):
    def __init__(self, ssh_credentials, async_run=False, **kwargs):
        super(SSHMode, self).__init__(**kwargs)
        self.ssh_cred = ssh_credentials
        self.async_run = async_run

    def run_script(self, script_filename):
        # subprocess
        cmd = self.ssh_cred.get_ssh_script_cmd(script_filename)
        shell.call(cmd, shell=True, wait=not self.async_run)


class DockerMode(LaunchMode):
    def __init__(self, 
                 docker_image='scratch',
                 docker_cmd='docker',
                 **kwargs):
        super(DockerMode, self).__init__(**kwargs)
        self.docker_image = docker_image
        self.docker_cmd = docker_cmd

    def run_script(self, script_filename):
        docker_cmd = '{docker_cmd} run {docker_img} -i /bin/{sh} -s < {script}'
        docker_cmd.format(
            docker_cmd=self.docker_cmd,
            docker_image=self.docker_image,
            sh=self.shell_interpreter,
            script=script_filename
        )
        shell.call(docker_cmd, shell=True, wait=True)
