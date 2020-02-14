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
    mounts = [gcp_mount]

    launcher = doodad.GCPMode(
        gcp_bucket=GCP_BUCKET,
        gcp_log_path='test_doodad/gcp_gpu_test',
        gcp_project=GCP_PROJECT,
        instance_type='n1-standard-1',
        zone='us-west1-a',
        gcp_image=GCP_IMAGE,
        gcp_image_project=GCP_PROJECT,
        use_gpu=True,
        gpu_model='nvidia-tesla-t4'
    )

    doodad.run_command(
        command='nvidia-smi > /output/secret.txt',
        mode=launcher,
        mounts=mounts,
        verbose=True
    )

if __name__ == '__main__':
    run()
