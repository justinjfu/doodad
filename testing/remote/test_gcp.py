import os
from doodad import mount, mode
from doodad.launch import launch_api
from doodad.utils import TESTING_DIR
from testing.config import GCP_PROJECT, GCP_BUCKET, GCP_IMAGE

def run():
    gcp_mount = mount.MountGCP(
        gcp_path='secret_output',
        mount_point='/output'
    )
    local_mount = mount.MountLocal(
        local_dir=TESTING_DIR,
        mount_point='/data',
        output=False
    )
    mounts = [local_mount, gcp_mount]

    launcher = mode.GCPMode(
        gcp_bucket=GCP_BUCKET,
        gcp_log_path='test_doodad/gcp_test',
        gcp_project=GCP_PROJECT,
        instance_type='f1-micro',
        zone='us-west1-a',
        gcp_image=GCP_IMAGE,
        gcp_image_project=GCP_PROJECT
    )

    launch_api.run_command(
        command='cat /data/secret.txt > /output/secret.txt',
        mode=launcher,
        mounts=mounts,
        verbose=True
    )

if __name__ == '__main__':
    run()
