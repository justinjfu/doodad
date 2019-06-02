import os
from datetime import datetime

import doodad
import doodad.mode
import doodad.mount as mount
from doodad.utils import REPO_DIR
from doodad.wrappers.sweeper import hyper_sweep



class DoodadSweeper(object):
    def __init__(self,
            mounts=None,
            docker_img='python:3',
            docker_output_dir='/data',
            local_output_dir='/data/docker',
            gcp_bucket_name=None,
            gcp_image=None,
            gcp_project=None,
            ):
        if mounts is None:
            mounts = []

        self.image = docker_img
        #self.python_cmd = python_cmd
        self.mode_local = doodad.mode.LocalMode()

        # always include doodad
        #mounts.append(mount.MountLocal(local_dir=REPO_DIR, pythonpath=True))
        self.docker_output_dir = docker_output_dir
        self.mounts = mounts
        self.mount_out_local = mount.MountLocal(local_dir=local_output_dir, mount_point=docker_output_dir, output=True)

        self.gcp_bucket_name = gcp_bucket_name
        self.gcp_image = gcp_image
        self.gcp_project = gcp_project
        self.mount_out_gcp = mount.MountGCP(gcp_path='exp_logs', mount_point=docker_output_dir, output=True)

    def run_test_local(self, target, params, extra_mounts=None, **kwargs):
        if extra_mounts is None:
            extra_mounts = []
        return hyper_sweep.run_sweep_doodad(target, params, run_mode=self.mode_local,
                         docker_image=self.image,
                         mounts=self.mounts+[self.mount_out_local]+extra_mounts,
                         test_one=True, **kwargs)

    def run_sweep_local(self, target, params, extra_mounts=None, num_chunks=-1, **kwargs):
        if extra_mounts is None:
            extra_mounts = []
        if num_chunks > 0:
            return hyper_sweep.run_sweep_doodad_chunked(target, params, run_mode=self.mode_local,
                         docker_image=self.image,
                         mounts=self.mounts+[self.mount_out_local]+extra_mounts,
                         num_chunks=num_chunks,
                         **kwargs)
        else:
            return hyper_sweep.run_sweep_doodad(target, params, run_mode=self.mode_local,
                         docker_image=self.image,
                         mounts=self.mounts+[self.mount_out_local]+extra_mounts,
                         **kwargs)

    def run_sweep_gcp(self, target, params, 
                      log_prefix=None, add_date_to_logname=True,
                      region='us-west1-a', instance_type='n1-standard-4', args=None,
                      extra_mounts=None, num_chunks=-1, **kwargs):
        if extra_mounts is None:
            extra_mounts = []
        if log_prefix is None:
            log_prefix = 'unnamed_experiment'
        if add_date_to_logname:
            datestamp = datetime.now().strftime('%Y_%m_%d')
            log_prefix = '%s_%s' % (datestamp, log_prefix)

        mode_ec2 = doodad.mode.GCPDocker(
            gcp_bucket=self.gcp_bucket_name,
            gcp_log_path=os.path.join('doodad/logs', log_prefix),
            gcp_project=self.gcp_project,
            zone=region,
            instance_type=instance_type,
            gcp_image=self.gcp_image,
            gcp_image_project=self.gcp_project
        )
        if num_chunks > 0:
            hyper_sweep.run_sweep_doodad_chunked(target, params, 
                    run_mode=mode_ec2, 
                    docker_image=self.image,
                    num_chunks=num_chunks,
                    mounts=self.mounts+[self.mount_out_gcp]+extra_mounts, 
                    **kwargs)
        else:
            hyper_sweep.run_sweep_doodad(target, params, 
                    run_mode=mode_ec2, 
                    docker_image=self.image,
                    mounts=self.mounts+[self.mount_out_gcp]+extra_mounts, 
                    **kwargs)

