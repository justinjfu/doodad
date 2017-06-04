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

MY_RUN_MODE = mode_docker  # CHANGE THIS

# Set up code and output directories
mounts = [
    mount.MountLocal(local_dir=REPO_DIR, pythonpath=True), # Code
]


THIS_FILE_DIR = os.path.realpath(os.path.dirname(__file__))
pd.launch_python(
    target=os.path.join(THIS_FILE_DIR, 'app_main.py'),  # point to a target script. If running remotely, this will be copied over
    mode=MY_RUN_MODE,
    mount_points=mounts,
    args={
        'arg1': 50,
    }
)

