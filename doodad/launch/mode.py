import json
import uuid

from doodad.utils import shell
from doodad.utils import safe_import
from doodad.darchive import mount

googleapiclient = safe_import.try_import('googleapiclient')
from doodad.apis import gcp_util 


class LaunchMode(object):
    def __init__(self, shell_interpreter='sh', async_run=False):
        self.shell_interpreter = shell_interpreter
        self.async_run = async_run

    def run_script(self, script_filename, dry=False, return_output=False):
        """
        Runs a shell script.
        """
        if return_output:
            output = shell.call_and_get_output(self.get_run_command(script_filename), shell=True, dry=dry)
            return output.decode('utf-8')
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


class GCPMode(LaunchMode):
    def __init__(self, 
                 gcp_project,
                 gce_log_mount,
                 gce_image='ubuntu-1804-bionic-v20181222',
                 gce_image_project='ubuntu-os-cloud',
                 disk_size='64Gb',
                 terminate_on_end=True,
                 preemptible=True,
                 zone='us-west1-a',
                 instance_type='n1-standard-1',
                 log_prefix='gcp_experiment',
                 **kwargs):
        super(GCPMode, self).__init__(**kwargs)
        self.gcp_project = gcp_project
        assert isinstance(gce_log_mount, mount.MountGCP)
        self.gce_log_mount = gce_log_mount
        self.gcp_log_prefix = log_prefix
        self.gce_image = gce_image
        self.gce_image_project = gce_image_project
        self.disk_size = disk_size
        self.terminate_on_end = terminate_on_end
        self.preemptible = preemptible
        self.zone = zone
        self.instance_type = instance_type
        self.compute = googleapiclient.discovery.build('compute', 'v1')

    def run_script(self, script, dry=False, return_output=False):
        if return_output:
            raise NotImplementedError()
        exp_name = "{}-{}".format(self.gcp_log_prefix, gcp_util.make_timekey())
        exp_prefix = self.gcp_log_prefix

        run_cmd = self.get_run_command(script)
        metadata = {
            'bucket_name': self.gce_log_mount.gcp_bucket,
            'docker_cmd': run_cmd,
            'terminate': json.dumps(self.terminate_on_end),
            'startup-script': open(gcp_util.GCP_STARTUP_SCRIPT_PATH, "r").read(),
            'shutdown-script': open(gcp_util.GCP_SHUTDOWN_SCRIPT_PATH, "r").read(),
        }
        # instance name must match regex '(?:[a-z](?:[-a-z0-9]{0,61}[a-z0-9])?)'">
        unique_name= "doodad" + str(uuid.uuid4()).replace("-", "")
        self.create_instance(metadata, unique_name, exp_name, exp_prefix)

    def create_instance(self, metadata, name, exp_name="", exp_prefix=""):
        image_response = self.compute.images().get(
            project=self.gce_image_project,
            image=self.gce_image,
        ).execute()
        source_disk_image = image_response['selfLink']
        config = {
            'name': name,
            'machineType': gcp_util.get_machine_type(self.zone, self.instance_type),
            'disks': [{
                    'boot': True,
                    'autoDelete': True,
                    'initializeParams': {
                        'sourceImage': source_disk_image,
                        'diskSizeGb': self.disk_size,
                    }
            }],
            'networkInterfaces': [{
                'network': 'global/networks/default',
                'accessConfigs': [
                    {'type': 'ONE_TO_ONE_NAT', 'name': 'External NAT'}
                ]
            }],
            'serviceAccounts': [{
                'email': 'default',
                'scopes': ['https://www.googleapis.com/auth/cloud-platform']
            }],
            'metadata': {
                'items': [
                    {'key': key, 'value': value}
                    for key, value in metadata.items()
                ]
            },
            'scheduling': {
                "onHostMaintenance": "terminate",
                "automaticRestart": False,
                "preemptible": self.preemptible,
            },
            "labels": {
                "exp_name": exp_name,
                "exp_prefix": exp_prefix,
            }
        }
        return self.compute.instances().insert(
            project=self.gcp_project,
            zone=self.zone,
            body=config
        ).execute()

    def get_run_command(self, script_filename):
        return '%s %s' % (self.shell_interpreter, script_filename)