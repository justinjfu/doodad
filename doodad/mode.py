import os
import json
import uuid
import six
import base64
import pprint
import shlex

from doodad.utils import shell
from doodad.utils import safe_import
from doodad import mount
from doodad.apis.ec2.autoconfig import Autoconfig
from doodad.credentials.ec2 import AWSCredentials

googleapiclient = safe_import.try_import('googleapiclient')
googleapiclient.discovery = safe_import.try_import('googleapiclient.discovery')
boto3 = safe_import.try_import('boto3')
botocore = safe_import.try_import('botocore')
from doodad.apis import gcp_util, aws_util


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

    def run_script(self, script_filename, dry=False, return_output=False, verbose=False):
        """
        Runs a shell script.

        Args:
            script_filename (str): A string path to a shell script.
            dry (bool): If True, prints commands to be run but does not run them.
            verbose (bool): Verbose mode
            return_output (bool): If True, returns stdout from the script as a string.
        """
        if return_output:
            output = shell.call_and_get_output(self._get_run_command(script_filename), shell=True, dry=dry)
            if output:
                return output.decode('utf-8')
        else:
            shell.call(self._get_run_command(script_filename), shell=True, dry=dry, wait=not self.async_run)

    def _get_run_command(self, script_filename):
        raise NotImplementedError()

    def print_launch_message(self):
        pass


class LocalMode(LaunchMode):
    """
    A LocalMode executes commands locally using the host computer's shell interpreter.
    """
    def __init__(self, **kwargs):
        super(LocalMode, self).__init__(**kwargs)

    def __str__(self):
        return 'LocalMode'

    def _get_run_command(self, script_filename):
        return '%s %s' % (self.shell_interpreter, script_filename)


class SSHMode(LaunchMode):
    def __init__(self, ssh_credentials, **kwargs):
        super(SSHMode, self).__init__(**kwargs)
        self.ssh_cred = ssh_credentials

    def _get_run_command(self, script_filename):
        return self.ssh_cred.get_ssh_script_cmd(script_filename, 
                                                shell_interpreter=self.shell_interpreter)


class EC2Mode(LaunchMode):
    def __init__(self, 
                 ec2_credentials,
                 s3_bucket,
                 s3_log_path,
                 s3_log_prefix='ec2_experiment',
                 ami_name=None,
                 terminate_on_end=True,
                 region='auto',
                 instance_type='r3.nano',
                 spot_price=0.0,
                 security_group_ids=None,
                 security_groups=None,
                 aws_key_name=None,
                 iam_instance_profile_name='doodad',
                 swap_size=4096,
                 **kwargs):
        super(EC2Mode, self).__init__(**kwargs)
        self.credentials = ec2_credentials
        self.s3_bucket = s3_bucket
        self.s3_log_path = s3_log_path
        self.s3_log_prefix = s3_log_prefix
        self.ami = ami_name
        self.terminate_on_end = terminate_on_end
        self.region = region
        self.instance_type = instance_type
        self.use_gpu = False
        self.spot_price = spot_price
        self.image_id = ami_name
        self.aws_key_name = aws_key_name
        self.iam_instance_profile_name = iam_instance_profile_name
        self.security_groups = security_groups
        self.security_group_ids = security_group_ids
        self.swap_size = swap_size
        self.sync_interval = 15
    
    def dedent(self, s):
        lines = [l.strip() for l in s.split('\n')]
        return '\n'.join(lines)

    def run_script(self, script_name, dry=False, return_output=False, verbose=False):
        assert not return_output

        default_config = dict(
            image_id=self.image_id,
            instance_type=self.instance_type,
            key_name=self.aws_key_name,
            spot_price=self.spot_price,
            iam_instance_profile_name=self.iam_instance_profile_name,
            security_groups=self.security_groups,
            security_group_ids=self.security_group_ids,
            network_interfaces=[],
        )
        aws_config = dict(default_config)
        time_key = gcp_util.make_timekey()
        exp_name = "{}-{}".format(self.s3_log_prefix, time_key)
        exp_prefix = self.s3_log_prefix

        s3_base_dir = os.path.join(self.s3_log_path, exp_prefix.replace("_", "-"), exp_name)
        s3_log_dir = os.path.join(s3_base_dir, 'logs')
        stdout_log_s3_path = os.path.join(s3_base_dir, 'stdout_$EC2_INSTANCE_ID.log')

        sio = six.StringIO()
        sio.write("#!/bin/bash\n")
        sio.write("truncate -s 0 /home/ubuntu/user_data.log\n")
        sio.write("{\n")
        sio.write('die() { status=$1; shift; echo "FATAL: $*"; exit $status; }\n')
        sio.write('EC2_INSTANCE_ID="`wget -q -O - http://169.254.169.254/latest/meta-data/instance-id`"\n')
        sio.write("""
            aws ec2 create-tags --resources $EC2_INSTANCE_ID --tags Key=Name,Value={exp_name} --region {aws_region}
        """.format(exp_name=exp_name, aws_region=self.region))
        sio.write("""
            aws ec2 create-tags --resources $EC2_INSTANCE_ID --tags Key=exp_prefix,Value={exp_prefix} --region {aws_region}
        """.format(exp_prefix=exp_prefix, aws_region=self.region))

        # Add swap file
        if self.use_gpu:
            swap_location = '/mnt/swapfile'
        else:
            swap_location = '/var/swap.1'
        sio.write(
            'sudo dd if=/dev/zero of={swap_location} bs=1M count={swap_size}\n'
            .format(swap_location=swap_location, swap_size=self.swap_size))
        sio.write('sudo mkswap {swap_location}\n'.format(swap_location=swap_location))
        sio.write('sudo chmod 600 {swap_location}\n'.format(swap_location=swap_location))
        sio.write('sudo swapon {swap_location}\n'.format(swap_location=swap_location))

        sio.write("service docker start\n")
        #sio.write("docker --config /home/ubuntu/.docker pull {docker_image}\n".format(docker_image=self.docker_image))
        sio.write("export AWS_DEFAULT_REGION={aws_region}\n".format(aws_region=self.s3_bucket))
        sio.write("""
            curl "https://s3.amazonaws.com/aws-cli/awscli-bundle.zip" -o "awscli-bundle.zip"
            unzip awscli-bundle.zip
            sudo ./awscli-bundle/install -i /usr/local/aws -b /usr/local/bin/aws
        """)

        # 1) Upload script and download it to remote
        aws_util.s3_upload(script_name, self.s3_bucket, 'doodad/mount', dry=dry)
        script_s3_filename = 's3://{bucket_name}/doodad/mount/{script_name}'.format(
            bucket_name=self.s3_bucket,
            script_name=script_name
        )
        sio.write('aws s3 cp {script_s3_filename} /tmp/remote_script.sh\n'.format(
            script_s3_filename=script_s3_filename
        ))

        # 2) Sync data 
        # In theory the ec2_local_dir could be some random directory,
        # but we make it the same as the mount directory for
        # convenience.
        #
        # ec2_local_dir: directory visible to ec2 spot instance
        # moint_point: directory visible to docker running inside ec2
        #               spot instance
        ec2_local_dir = '/doodad'

        # Sync interval
        sio.write("""
        while /bin/true; do
            aws s3 sync --exclude '*' {include_string} {log_dir} {s3_path}
            sleep {periodic_sync_interval}
        done & echo sync initiated
        """.format(
            include_string='',
            log_dir=ec2_local_dir,
            s3_path=s3_log_dir,
            periodic_sync_interval=self.sync_interval
        ))

        # Sync on terminate. This catches the case where the spot
        # instance gets terminated before the user script ends.
        #
        # This is hoping that there's at least 3 seconds between when
        # the spot instance gets marked for  termination and when it
        # actually terminates.
        sio.write("""
            while /bin/true; do
                if [ -z $(curl -Is http://169.254.169.254/latest/meta-data/spot/termination-time | head -1 | grep 404 | cut -d \  -f 2) ]
                then
                    logger "Running shutdown hook."
                    aws s3 cp --recursive {log_dir} {s3_path}
                    aws s3 cp /home/ubuntu/user_data.log {stdout_log_s3_path}
                    break
                else
                    # Spot instance not yet marked for termination.
                    # This is hoping that there's at least 3 seconds
                    # between when the spot instance gets marked for
                    # termination and when it actually terminates.
                    sleep 3
                fi
            done & echo log sync initiated
        """.format(
            log_dir=ec2_local_dir,
            s3_path=s3_log_dir,
            stdout_log_s3_path=stdout_log_s3_path,
        ))

        sio.write("""
        while /bin/true; do
            aws s3 cp /home/ubuntu/user_data.log {stdout_log_s3_path}
            sleep {periodic_sync_interval}
        done & echo sync initiated
        """.format(
            stdout_log_s3_path=stdout_log_s3_path,
            periodic_sync_interval=self.sync_interval
        ))

        if self.use_gpu:
            sio.write("""
                for i in {1..800}; do su -c "nvidia-modprobe -u -c=0" ubuntu && break || sleep 3; done
                systemctl start nvidia-docker
            """)
            sio.write("echo 'Testing nvidia-smi'\n")
            sio.write("nvidia-smi\n")
            sio.write("echo 'Testing nvidia-smi inside docker'\n")
            #sio.write("nvidia-docker run --rm {docker_image} nvidia-smi\n".format(docker_image=self.docker_image))

        #docker_cmd = self.get_docker_cmd(main_cmd, use_tty=False, extra_args=mnt_args, pythonpath=py_path, use_docker_generated_name=True)

        docker_cmd = '%s /tmp/remote_script.sh' % self.shell_interpreter
        sio.write(docker_cmd+'\n')

        # Sync all output mounts to s3 after running the user script
        # Ideally the earlier while loop would be sufficient, but it might be
        # the case that the earlier while loop isn't fast enough to catch a
        # termination. So, we explicitly sync on termination.
        sio.write("aws s3 cp --recursive {local_dir} {s3_dir}\n".format(
            local_dir=ec2_local_dir,
            s3_dir=s3_log_dir
        ))
        sio.write("aws s3 cp /home/ubuntu/user_data.log {}\n".format(
            stdout_log_s3_path,
        ))

        if self.terminate_on_end:
            sio.write("""
                EC2_INSTANCE_ID="`wget -q -O - http://169.254.169.254/latest/meta-data/instance-id || die \"wget instance-id has failed: $?\"`"
                aws ec2 terminate-instances --instance-ids $EC2_INSTANCE_ID --region {aws_region}
            """.format(aws_region=self.region))
        sio.write("} >> /home/ubuntu/user_data.log 2>&1\n")

        full_script = self.dedent(sio.getvalue())
        ec2 = boto3.client(
            "ec2",
            region_name=self.region,
            aws_access_key_id=self.credentials.aws_key,
            aws_secret_access_key=self.credentials.aws_secret_key,
        )

        if len(full_script) > 10000 or len(base64.b64encode(full_script.encode()).decode("utf-8")) > 10000:
            s3_path = aws_util.s3_upload(full_script, self.s3_bucket, 'doodad/mount', dry=dry)
            sio = six.StringIO()
            sio.write("#!/bin/bash\n")
            sio.write("""
            aws s3 cp {s3_path} /home/ubuntu/remote_script.sh --region {aws_region} && \\
            chmod +x /home/ubuntu/remote_script.sh && \\
            bash /home/ubuntu/remote_script.sh
            """.format(s3_path=s3_path, aws_region=self.s3_bucket))
            user_data = self.dedent(sio.getvalue())
        else:
            user_data = full_script

        if verbose:
            print(full_script)
            with open("/tmp/full_ec2_script", "w") as f:
                f.write(full_script)

        instance_args = dict(
            ImageId=aws_config["image_id"],
            KeyName=aws_config["key_name"],
            UserData=user_data,
            InstanceType=aws_config["instance_type"],
            EbsOptimized=False,
            SecurityGroups=aws_config["security_groups"],
            SecurityGroupIds=aws_config["security_group_ids"],
            NetworkInterfaces=aws_config["network_interfaces"],
            IamInstanceProfile=dict(
                Name=aws_config["iam_instance_profile_name"],
            ),
            #**config.AWS_EXTRA_CONFIGS,
        )

        if verbose:
            print("************************************************************")
            print('UserData:', instance_args["UserData"])
            print("************************************************************")
        instance_args["UserData"] = base64.b64encode(instance_args["UserData"].encode()).decode("utf-8")
        spot_args = dict(
            DryRun=dry,
            InstanceCount=1,
            LaunchSpecification=instance_args,
            SpotPrice=aws_config["spot_price"],
            # ClientToken=params_list[0]["exp_name"],
        )

        if verbose:
            pprint.pprint(spot_args)
        if not dry:
            response = ec2.request_spot_instances(**spot_args)
            print('Launched EC2 job - Server response:')
            pprint.pprint(response)
            print('*****'*5)
            spot_request_id = response['SpotInstanceRequests'][
                0]['SpotInstanceRequestId']
            for _ in range(10):
                try:
                    ec2.create_tags(
                        Resources=[spot_request_id],
                        Tags=[
                            {'Key': 'Name', 'Value': exp_name}
                        ],
                    )
                    break
                except botocore.exceptions.ClientError:
                    continue


class EC2Autoconfig(EC2Mode):
    def __init__(self,
            autoconfig_file=None,
            region='us-west-1',
            s3_bucket=None,
            ami_image=None,
            aws_key_name=None,
            iam_instance_profile_name=None,
            **kwargs
            ):
        # find config file
        autoconfig = Autoconfig(autoconfig_file)
        s3_bucket = autoconfig.s3_bucket() if s3_bucket is None else s3_bucket
        image_id = autoconfig.aws_image_id(region) if ami_image is None else ami_image
        aws_key_name= autoconfig.aws_key_name(region) if aws_key_name is None else aws_key_name
        iam_profile= autoconfig.iam_profile_name() if iam_instance_profile_name is None else iam_instance_profile_name
        credentials=AWSCredentials(aws_key=autoconfig.aws_access_key(), aws_secret=autoconfig.aws_access_secret())
        security_group_ids = autoconfig.aws_security_group_ids()[region]
        security_groups = autoconfig.aws_security_groups()

        super(EC2Autoconfig, self).__init__(
                s3_bucket=s3_bucket,
                ami_name=image_id,
                aws_key_name=aws_key_name,
                iam_instance_profile_name=iam_profile,
                ec2_credentials=credentials,
                region=region,
                security_groups=security_groups,
                security_group_ids=security_group_ids,
                **kwargs
                )


class GCPMode(LaunchMode):
    """
    GCP Launch Mode.

    Args:
        gcp_project (str): Name of GCP project to launch from
        gcp_bucket (str): GCP Bucket for storing logs and data
        gcp_log_path (str): Path under GCP bucket to store logs/data.
            The full path will be of the form:
            gs://{gcp_bucket}/{gcp_log_path}
        gcp_image (str): Name of GCE image from which to base instance.
        gcp_image_project (str): Name of project gce_image belongs to.
        disk_size (int): Amount of disk to allocate to instance in Gb.
        terminate_on_end (bool): Terminate instance when script finishes
        preemptible (bool): Start a preemptible instance
        zone (str): GCE compute zone.
        instance_type (str): GCE instance type
    """
    def __init__(self, 
                 gcp_project,
                 gcp_bucket,
                 gcp_log_path,
                 gcp_image='ubuntu-1804-bionic-v20181222',
                 gcp_image_project='ubuntu-os-cloud',
                 disk_size=64,
                 terminate_on_end=True,
                 preemptible=True,
                 zone='auto',
                 instance_type='f1-micro',
                 gcp_label='gcp_doodad',
                 **kwargs):
        super(GCPMode, self).__init__(**kwargs)
        self.gcp_project = gcp_project
        self.gcp_bucket = gcp_bucket
        self.gcp_log_path = gcp_log_path
        self.gce_image = gcp_image
        self.gce_image_project = gcp_image_project
        self.disk_size = disk_size
        self.terminate_on_end = terminate_on_end
        self.preemptible = preemptible
        self.zone = zone
        self.instance_type = instance_type
        self.use_gpu = False
        self.gcp_label = gcp_label
        self.compute = googleapiclient.discovery.build('compute', 'v1')

    def __str__(self):
        return 'GCP-%s-%s' % (self.gcp_project, self.instance_type)

    def print_launch_message(self):
        print('Go to https://console.cloud.google.com/compute to monitor jobs.')

    def run_script(self, script, dry=False, return_output=False, verbose=False):
        if return_output:
            raise NotImplementedError()

        # Upload script to GCS
        cmd_split = shlex.split(script)
        script_fname = cmd_split[0]
        if len(cmd_split) > 1:
            script_args = ' '.join(cmd_split[1:])
        else:
            script_args = ''
        remote_script = gcp_util.upload_file_to_gcp_storage(self.gcp_bucket, script_fname, dry=dry)

        exp_name = "{}-{}".format(self.gcp_label, gcp_util.make_timekey())
        exp_prefix = self.gcp_label

        with open(gcp_util.GCP_STARTUP_SCRIPT_PATH) as f:
            start_script = f.read()
        with open(gcp_util.GCP_SHUTDOWN_SCRIPT_PATH) as f:
            stop_script = f.read()

        metadata = {
            'shell_interpreter': self.shell_interpreter,
            'gcp_bucket_path': self.gcp_log_path,
            'remote_script_path': remote_script,
            'bucket_name': self.gcp_bucket,
            'terminate': json.dumps(self.terminate_on_end),
            'use_gpu': self.use_gpu,
            'script_args': script_args,
            'startup-script': start_script,
            'shutdown-script': stop_script
        }
        # instance name must match regex '(?:[a-z](?:[-a-z0-9]{0,61}[a-z0-9])?)'">
        unique_name= "doodad" + str(uuid.uuid4()).replace("-", "")
        instance_info = self.create_instance(metadata, unique_name, exp_name, exp_prefix, dry=dry)
        if verbose:
            print('Launched instance %s' % unique_name)
            print(instance_info)
        return metadata

    def create_instance(self, metadata, name, exp_name="", exp_prefix="", dry=False):
        compute_images = self.compute.images().get(
            project=self.gce_image_project,
            image=self.gce_image,
        )
        if not dry:
            image_response = compute_images.execute()
        else:
            image_response = {'selfLink': None}
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
