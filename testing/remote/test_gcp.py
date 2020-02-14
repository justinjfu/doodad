"""
Instructions:

1) Set up testing/config.py (copy from config.py.example and fill in the fields)
2) Run this script
3) Look inside your GCP_BUCKET under test_doodad and you should see results in secret.txt
"""
import os
import doodad
from doodad.utils import TESTING_DIR
from testing.config import GCP_PROJECT, GCP_BUCKET, GCP_IMAGE

def run():
    gcp_mount = doodad.MountGCP(
        gcp_path='secret_output',
        mount_point='/output'
    )
    local_mount = doodad.MountLocal(
        local_dir=TESTING_DIR,
        mount_point='/data',
        output=False
    )
    mounts = [local_mount, gcp_mount]

    launcher = doodad.GCPMode(
        gcp_bucket=GCP_BUCKET,
        gcp_log_path='test_doodad/gcp_test',
        gcp_project=GCP_PROJECT,
        instance_type='f1-micro',
        zone='us-west1-a',
        gcp_image=GCP_IMAGE,
        gcp_image_project=GCP_PROJECT
    )

    doodad.run_command(
        command='cat /data/secret.txt > /output/secret.txt',
        mode=launcher,
        mounts=mounts,
        verbose=True
    )

if __name__ == '__main__':
    run()
