import os
from doodad import mount, mode
from doodad.launch import launch_api
from doodad.utils import TESTING_DIR
from testing.config import S3_BUCKET

def run():
    ec2_mount = mount.MountS3(
        s3_path='secret_output',
        mount_point='/output'
    )
    local_mount = mount.MountLocal(
        local_dir=TESTING_DIR,
        mount_point='/data',
        output=False
    )
    mounts = [local_mount, ec2_mount]

    launcher = mode.EC2Autoconfig(
        s3_bucket=S3_BUCKET,
        s3_log_path='test_doodad/ec2_test',
        instance_type='t3a.micro',
        spot_price=0.03,
        region='us-east-2',
        ami_name='ami-0aa0375ca68b5554d',
    )

    #launch_api.run_command(
    #    command='cat /data/secret.txt > /output/secret.txt',
    #    mode=launcher,
    #    mounts=mounts,
    #    verbose=True
    #)

    launch_api.run_python(
        target='testing/remote/py_print.py',
        cli_args='--message=test_args123',
        mode=launcher,
        verbose=True
    )

if __name__ == '__main__':
    run()
