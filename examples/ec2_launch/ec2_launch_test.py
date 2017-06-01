import os

import poodag as pd
import poodag.ec2 as ec2
import poodag.ssh as ssh
import poodag.mount as mount
from poodag.utils import EXAMPLES_DIR, REPO_DIR


# Local run
mode_local = pd.mode.Local()

# Local docker
mode_docker = pd.mode.LocalDocker(
    image='python:3.5',
)

# or this! Run experiment via docker on another machine through SSH
mode_ssh = pd.mode.SSHDocker(
    image='python:3.5',
    credentials=ssh.SSHCredentials(hostname='my.machine.name', username='my_username', identity_file='~/.ssh/id_rsa'),
)

# or use this! 
mode_ec2 = pd.mode.EC2AutoconfigDocker(
    image='python:3.5',
    region='us-west-1',
    instance_type='m3.medium',
    spot_price=0.02,
)

MY_RUN_MODE = mode_ec2  # CHANGE THIS

# Set up code and output directories
OUTPUT_DIR = '/example/outputs'  # this is the directory visible to the target 
mounts = [
    mount.MountLocal(local_dir=REPO_DIR, pythonpath=True), # Code
    mount.MountLocal(local_dir=os.path.join(EXAMPLES_DIR, 'secretlib', pythonpath=True), # Code
]

if MY_RUN_MODE == mode_ec2:
    output_mount = mount.MountS3(s3_path='outputs', mount_point=OUTPUT_DIR, output=True)  # use this for ec2
else:
    output_mount = mount.MountLocal(local_dir=os.path.join(EXAMPLES_DIR, 'tmp_output'), 
        mount_point=OUTPUT_DIR, read_only=False), #Output directory - set read_only=False
mounts.append(output_mount)


THIS_FILE_DIR = os.path.realpath(os.path.dirname(__file__))
pd.launch_python(
    target=os.path.join(THIS_FILE_DIR, 'app_main.py'),  # point to a target script. If running remotely, this will be copied over
    mode=MY_RUN_MODE,
    mount_points=mounts,
    args={
        'arg1': 50,
        'arg2': 25,
        'output_dir': OUTPUT_DIR,
    }
)

