import json
import uuid

from doodad.utils import shell
from doodad.utils import safe_import
from doodad.darchive import mount

googleapiclient = safe_import.try_import('googleapiclient')
googleapiclient.discovery = safe_import.try_import('googleapiclient.discovery')
from doodad.apis import gcp_util 


class LaunchMode(object):
    """
    A LaunchMode object is responsible for executing a shell script on a specified platform.

    Args:
        shell_interpreter (str): Interpreter command for script. Default 'sh'
        async_run (bool): If True, 
    """
    def __init__(self, shell_interpreter='sh', async_run=False):
        self.shell_interpreter = shell_interpreter
        self.async_run = async_run

    def run_script(self, script_filename, dry=False, return_output=False):
        """
        Runs a shell script.

        Args:
            script_filename (str): A string path to a shell script.
            dry (bool): If True, prints commands to be run but does not run them.
            return_output (bool): If True, returns stdout from the script as a string.
        """
        if return_output:
            output = shell.call_and_get_output(self._get_run_command(script_filename), shell=True, dry=dry)
            return output.decode('utf-8')
        else:
            shell.call(self._get_run_command(script_filename), shell=True, dry=dry, wait=not self.async_run)

    def _get_run_command(self, script_filename):
        raise NotImplementedError()


class LocalMode(LaunchMode):
    """
    A LocalMode executes commands locally using the host computer's shell interpreter.
    """
    def __init__(self, **kwargs):
        super(LocalMode, self).__init__(**kwargs)

    def _get_run_command(self, script_filename):
        return '%s %s' % (self.shell_interpreter, script_filename)


class SSHMode(LaunchMode):
    def __init__(self, ssh_credentials, **kwargs):
        super(SSHMode, self).__init__(**kwargs)
        self.ssh_cred = ssh_credentials

    def _get_run_command(self, script_filename):
        return self.ssh_cred.get_ssh_script_cmd(script_filename)


class GCPMode(LaunchMode):
    """
    GCP Launch Mode.

    Args:
        gcp_project (str): Name of GCP project to launch from
        gcp_log_mount (str): A MountGCP object for logging stdout information.
        gce_image (str): Name of GCE image from which to base instance.
        gce_image_project (str): Name of project gce_image belongs to.
        disk_size (int): Amount of disk to allocate to instance in Gb.
        terminate_on_end (bool): Terminate instance when script finishes
        preemptible (bool): Start a preemptible instance
        zone (str): GCE compute zone.
        instance_type (str): GCE instance type
    """
    def __init__(self, 
                 gcp_project,
                 gcp_log_mount,
                 gce_image='ubuntu-1804-bionic-v20181222',
                 gce_image_project='ubuntu-os-cloud',
                 disk_size=64,
                 terminate_on_end=True,
                 preemptible=True,
                 zone='auto',
                 instance_type='n1-standard-1',
                 log_prefix='gcp_experiment',
                 **kwargs):
        super(GCPMode, self).__init__(**kwargs)
        self.gcp_project = gcp_project
        assert isinstance(gcp_log_mount, mount.MountGCP)
        self.gce_log_mount = gcp_log_mount
        self.gcp_bucket = gcp_log_mount.gcp_bucket
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

        # Upload script to GCS
        remote_script = gcp_util.upload_file_to_gcp_storage(self.gcp_bucket, script, dry=dry)

        exp_name = "{}-{}".format(self.gcp_log_prefix, gcp_util.make_timekey())
        exp_prefix = self.gcp_log_prefix

        metadata = {
            'shell_interpreter': self.shell_interpreter,
            'gcp_bucket_path': self.gce_log_mount.gcp_path,
            'script_path': remote_script,
            'bucket_name': self.gce_log_mount.gcp_bucket,
            'terminate': json.dumps(self.terminate_on_end),
            'startup-script': open(gcp_util.GCP_STARTUP_SCRIPT_PATH, "r").read(),
            'shutdown-script': open(gcp_util.GCP_SHUTDOWN_SCRIPT_PATH, "r").read(),
        }
        # instance name must match regex '(?:[a-z](?:[-a-z0-9]{0,61}[a-z0-9])?)'">
        unique_name= "doodad" + str(uuid.uuid4()).replace("-", "")
        self.create_instance(metadata, unique_name, exp_name, exp_prefix, dry=dry)
        return metadata

    def create_instance(self, metadata, name, exp_name="", exp_prefix="", dry=False):
        image_response = self.compute.images().get(
            project=self.gce_image_project,
            image=self.gce_image,
        ).execute()
        source_disk_image = image_response['selfLink']
        if self.zone == 'auto':
            raise NotImplementedError('auto zone finder')
        zone = self.zone

        config = {
            'name': name,
            'machineType': gcp_util.get_machine_type(zone, self.instance_type),
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
        compute_instances = self.compute.instances().insert(
            project=self.gcp_project,
            zone=zone,
            body=config
        )
        if not dry:
            return compute_instances.execute()
