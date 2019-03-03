from datetime import datetime

import doodad
import doodad.mode
import doodad.mount as mount
from doodad.utils import REPO_DIR
from doodad.wrappers.sweeper.hyper_sweep import run_sweep_doodad  


class DoodadSweeper(object):
    def __init__(self,
            mounts,
            docker_img='python:3',
            docker_output_dir='/data',
            local_output_dir='data/docker',
            gcp_bucket_name=None,
            gcp_image=None,
            gcp_project=None,
            ):

        self.image = docker_img
        self.python_cmd = python_cmd
        self.mode_local = doodad.mode.LocalDocker(image=docker_img)

        # always include doodad
        mounts.append(mount.MountLocal(local_dir=REPO_DIR, pythonpath=True))
        self.docker_output_dir = docker_output_dir
        self.mounts = mounts
        self.mount_out_local = mount.MountLocal(local_dir=local_output_dir, mount_point=docker_output_dir, output=True)
        # self.mount_out_s3 = mount.MountS3(s3_path='exp_logs', mount_point=docker_output_dir, output=True)

        self.gcp_bucket_name = gcp_bucket_name
        self.gcp_image = gcp_image
        self.gcp_project = gcp_project
        self.mount_out_gcp = mount.MountGCP(gcp_path='exp_logs', gcp_bucket_name=gcp_bucket_name, mount_point=docker_output_dir, output=True)

    def run_test_local(self, target, params, args=None, extra_mounts=None):
        if extra_mounts is None:
            extra_mounts = []
        self.mode_local.async = False
        run_sweep_doodad(target, params, run_mode=self.mode_local,
                         docker_image=self.image,
                         mounts=self.mounts+[self.mount_out_local]+extra_mounts,
                         test_one=True, args=args)

    def run_sweep_local(self, target, params, args=None, extra_mounts=None):
        if extra_mounts is None:
            extra_mounts = []
        self.mode_local.async = False
        run_sweep_doodad(target, params, run_mode=self.mode_local,
                         docker_image=self.image,
                         mounts=self.mounts+[self.mount_out_local]+extra_mounts,
                         args=args)

    def run_sweep_gcp(self, target, params, 
                      s3_log_name=None, add_date_to_logname=True,
                      region='us-west1-a', instance_type='n1-standard-4', repeat=1, args=None,
                      extra_mounts=None):
        if extra_mounts is None:
            extra_mounts = []
        if s3_log_name is None:
            s3_log_name = 'unnamed_experiment'
        if add_date_to_logname:
            datestamp = datetime.now().strftime('%Y_%m_%d')
            s3_log_name = '%s_%s' % (datestamp, s3_log_name)

        mode_ec2 = doodad.mode.GCPDocker(
            zone=region,
            gcp_bucket_name=self.gcp_bucket_name,
            instance_type=instance_type,
            gcp_log_prefix=s3_log_name,
            image_name=self.gcp_image,
            image_project=self.gcp_project,
        )
        run_sweep_doodad(target, params, run_mode=mode_ec2, 
                docker_image=self.image,
                mounts=self.mounts+[self.mount_out_gcp]+extra_mounts, 
                repeat=repeat, args=args)

