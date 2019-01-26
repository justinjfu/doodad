import os
import time

from doodad.utils import hash_file, REPO_DIR, safe_import
storage = safe_import.try_import('google.cloud.storage')

GCP_STARTUP_SCRIPT_PATH = os.path.join(REPO_DIR, "scripts/gcp/gcp_startup_script.sh")
GCP_SHUTDOWN_SCRIPT_PATH = os.path.join(REPO_DIR, "scripts/gcp/gcp_shutdown_script.sh")

def make_timekey():
        return '%d'%(int(time.time()*1000))

def upload_file_to_gcp_storage(
    bucket_name,
    file_name,
    remote_filename=None,
    dry=False,
    check_exists=True
):
    if remote_filename is None:
        remote_filename = os.path.basename(file_name)
    remote_path = 'doodad/mount/' + remote_filename
    if not dry:
        storage_client = storage.Client()
        bucket = storage_client.get_bucket(bucket_name)
        blob = bucket.blob(remote_path)
        if check_exists and blob.exists(storage_client):
            print("{remote_path} already exists".format(remote_path=remote_path))
            return remote_path
        blob.upload_from_filename(file_name)
    return remote_path

def get_machine_type(zone, instance_type):
    return "zones/{zone}/machineTypes/{instance_type}".format(
            zone=zone,
            instance_type=instance_type,
    )

def get_gpu_type(project, zone, gpu_model):
    """
    Check the available gpu models for each zone
    https://cloud.google.com/compute/docs/gpus/
    """
    assert gpu_model in [
        'nvidia-tesla-p4',
        'nvidia-tesla-k80',
        'nvidia-tesla-v100',
        'nvidia-tesla-p100'
    ]

    return (
        "https://www.googleapis.com/compute/v1/"
        "projects/{project}/zones/{zone}/acceleratorTypes/{gpu_model}".format(
            project=project,
            zone=zone,
            gpu_model=gpu_model
        )
    )
