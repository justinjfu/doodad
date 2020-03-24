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
        s3_log_path='test_doodad/gcp_test',
        instance_type='c4.large',
        spot_price=0.03,
        region='us-west-1',
        ami_name='ami-874378e7',
    )

    launch_api.run_command(
        command='cat /data/secret.txt > /output/secret.txt',
        mode=launcher,
        mounts=mounts,
        verbose=True
    )

if __name__ == '__main__':
    run()
