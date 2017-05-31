import os
import subprocess
import tempfile
import uuid
import time
import base64
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

from .mount import *

class LaunchMode(object):
    def launch_command(self, cmd, mount_points=None, dry=False):
        raise NotImplementedError()


def call_and_wait(cmd, verbose=False, dry=False):
    if dry or verbose:
        print(cmd)
    if not dry:
        p = subprocess.Popen(cmd, shell=True)
    try:
        p.wait()
    except KeyboardInterrupt:
        try:
            print("terminating")
            p.terminate()
        except OSError:
            print("os error!")
            pass
        p.wait()


class Local(LaunchMode):
    def __init__(self):
        super(Local, self).__init__()
        self.env = {}

    def launch_command(self, cmd, mount_points=None, dry=False):
        if dry: 
            print(cmd); return

        cmd_list = []
        # chdir to home dir
        cmd_list.append('cd %s' % (os.path.expanduser('~')))

        # do mounting
        py_path = []
        cleanup_commands = []
        for mount in mount_points:
            if isinstance(mount, MountLocal):
                if not mount.no_remount:
                    mount.create_if_nonexistent()
                    cmd_list.append('ln -s %s %s' % (mount.local_dir, mount.mount_point))
                    #subprocess.call(symlink_cmd, shell=True)
                    if mount.cleanup:
                        cleanup_commands.append('rm "%s"' % mount.mount_point)
                if mount.pythonpath:
                    py_path.append(mount.mount_point)
            else:
                raise NotImplementedError()

        # add pythonpath mounts
        if py_path:
            cmd_list.append('export PYTHONPATH=$PYTHONPATH:%s' % (':'.join(py_path)))

        # Add main command
        cmd_list.append(cmd)

        # cleanup
        for clean_cmd in cleanup_commands:
            cmd_list.append(clean_cmd)

        # Call everything
        #print('DEBUG: commands:', cmd_list)
        subprocess.call(';'.join(cmd_list), shell=True, env=dict(os.environ, **self.env))

LOCAL = Local()


class DockerMode(LaunchMode):
    def __init__(self, image='ubuntu:16.04'):
        super(DockerMode, self).__init__()
        self.docker_image = image

    def get_docker_cmd(self, main_cmd, extra_args='', use_tty=True, verbose=True, pythonpath=None, pre_cmd=None, post_cmd=None):
        cmd_list= []
        if pre_cmd:
            cmd_list.extend(pre_cmd)
        if verbose:
            cmd_list.append('echo \"Running in docker\"')
        if pythonpath:
            cmd_list.append('export PYTHONPATH=$PYTHONPATH:%s' % (':'.join(pythonpath)))
        cmd_list.append(main_cmd)
        if post_cmd:
            cmd_list.extend(post_cmd)
        if use_tty:
            docker_prefix = 'docker run %s -ti %s /bin/bash -c ' % (extra_args, self.docker_image)
        else:
            docker_prefix = 'docker run %s -t %s /bin/bash -c ' % (extra_args, self.docker_image)
        main_cmd = ';'.join(cmd_list)
        full_cmd = docker_prefix + ("\'%s\'" % main_cmd)
        return full_cmd


class LocalDocker(DockerMode):
    def __init__(self, **kwargs):
        super(LocalDocker, self).__init__(**kwargs)

    def launch_command(self, cmd, mount_points=None, dry=False):
        mnt_args = ''
        py_path = []
        for mount in mount_points:
            if isinstance(mount, MountLocal):
                mnt_args += ' -v %s:%s' % (mount.local_dir, mount.mount_point)
                if mount.pythonpath:
                    py_path.append(mount.mount_point)
            else:
                raise NotImplementedError()
        full_cmd = self.get_docker_cmd(cmd, extra_args=mnt_args, pythonpath=py_path)
        call_and_wait(full_cmd, dry=dry)


class SSHDocker(DockerMode):
    TMP_DIR = '~/.poodag_tmp'

    def __init__(self, credentials=None, **docker_args):
        super(SSHDocker, self).__init__(**docker_args)
        self.credentials = credentials

    def launch_command(self, main_cmd, mount_points=None, dry=False, verbose=True):
        py_path = []
        remote_cmds = []
        remote_cleanup_commands = []
        mnt_args = ''

        tmp_dir_cmd = 'mkdir -p %s' % SSHDocker.TMP_DIR
        tmp_dir_cmd = self.credentials.get_ssh_bash_cmd(tmp_dir_cmd)
        call_and_wait(tmp_dir_cmd, dry=dry, verbose=verbose)

        # SCP Code over
        # TODO: add feature for no scp if hashes match
        for mount in mount_points:
            if isinstance(mount, MountLocal):
                if mount.read_only:
                    with mount.gzip() as gzip_file:
                        # scp
                        remote_name = os.path.join(SSHDocker.TMP_DIR, os.path.basename(gzip_file))
                        scp_cmd = self.credentials.get_scp_cmd(gzip_file, remote_name)
                        call_and_wait(scp_cmd, dry=dry, verbose=verbose)
                    unzip_cmd = 'tar -xf %s -C %s' % (remote_name, SSHDocker.TMP_DIR)
                    remote_cmds.append(unzip_cmd)
                    mount_point =  os.path.join('/mounts', mount.mount_point.replace('~/',''))
                    mnt_args += ' -v %s:%s' % (os.path.splitext(remote_name)[0],mount_point)
                else:
                    #remote_cmds.append('mkdir -p %s' % mount.mount_point)
                    mnt_args += ' -v %s:%s' % (mount.local_dir_raw, mount.mount_point)

                if mount.pythonpath:
                    py_path.append(mount_point)
            else:
                raise NotImplementedError()

        docker_cmd = self.get_docker_cmd(main_cmd, use_tty=False, extra_args=mnt_args, pythonpath=py_path)

        remote_cmds.append(docker_cmd)
        remote_cmds.extend(remote_cleanup_commands)

        with tempfile.NamedTemporaryFile('w+', suffix='.sh') as ntf:
            for cmd in remote_cmds:
                if verbose:
                    ntf.write('echo "%s$ %s"\n' % (self.credentials.user_host, cmd)) 
                ntf.write(cmd+'\n')
            ntf.seek(0)
            ssh_cmd = self.credentials.get_ssh_script_cmd(ntf.name)

            call_and_wait(ssh_cmd, dry=dry, verbose=verbose)


def dedent(s):
    lines = [l.strip() for l in s.split('\n')]
    return '\n'.join(lines)

class EC2SpotDocker(DockerMode):
    def __init__(self, 
            credentials,
            region='us-west-1',
            instance_type='m1.small',
            spot_price=0.0,
            s3_bucket=None,
            terminate=True,
            image_id=None,
            aws_key_name=None,
            s3_exp_prefix='experiment',
            **kwargs
            ):
        super(EC2SpotDocker, self).__init__(**kwargs)
        self.credentials = credentials
        self.region = region
        self.spot_price = str(float(spot_price))
        self.instance_type = instance_type
        self.terminate = terminate
        self.s3_bucket = s3_bucket
        self.image_id = image_id
        self.aws_key_name = aws_key_name
        self.s3_exp_prefix = 'experiment'

        self.s3_mount_path = 's3://%s/poodag/mount' % self.s3_bucket
        self.aws_s3_path = 's3://%s/poodag/logs' % self.s3_bucket

    def upload_file_to_s3(script_content):
        f = tempfile.NamedTemporaryFile(delete=False)
        f.write(script_content.encode())
        f.close()
        remote_path = os.path.join(self.s3_mount_path, 'oversize_bash_scripts', str(uuid.uuid4()))
        subprocess.check_call(["aws", "s3", "cp", f.name, remote_path])
        os.unlink(f.name)
        return remote_path

    def s3_upload(self, file_name, dry=False):
        base = self.s3_mount_path
        remote_path = "%s/%s" % (base, os.path.basename(file_name))
        upload_cmd = ["aws", "s3", "cp", file_name, remote_path]
        print(" ".join(upload_cmd))
        if not dry:
            subprocess.check_call(upload_cmd)
        return remote_path

    def make_timekey(self):
        return '_%d'%(int(time.time()*1000))

    def launch_command(self, main_cmd, mount_points=None, dry=False, verbose=True):
        #dry=True #DRY

        default_config = dict(
            image_id=self.image_id,
            instance_type=self.instance_type,
            key_name=self.aws_key_name,
            spot_price=self.spot_price,
            iam_instance_profile_name='rllab', #config.AWS_IAM_INSTANCE_PROFILE_NAME,
            security_groups=[], #config.AWS_SECURITY_GROUPS,
            security_group_ids=[], #config.AWS_SECURITY_GROUP_IDS,
            network_interfaces=[], #config.AWS_NETWORK_INTERFACES,
        )
        aws_config = dict(default_config)
        exp_name = 'run'+self.make_timekey()
        exp_prefix = self.s3_exp_prefix
        remote_log_dir = os.path.join(self.aws_s3_path, exp_prefix.replace("_", "-"), exp_name)
        log_dir = "/tmp/expt/local/" + exp_prefix.replace("_", "-") + "/" + exp_name

        sio = StringIO()
        sio.write("#!/bin/bash\n")
        sio.write("{\n")
        sio.write('die() { status=$1; shift; echo "FATAL: $*"; exit $status; }\n')
        sio.write('EC2_INSTANCE_ID="`wget -q -O - http://169.254.169.254/latest/meta-data/instance-id`"\n')
        sio.write("""
            aws ec2 create-tags --resources $EC2_INSTANCE_ID --tags Key=Name,Value={exp_name} --region {aws_region}
        """.format(exp_name=exp_name, aws_region=self.region))
        sio.write("""
            aws ec2 create-tags --resources $EC2_INSTANCE_ID --tags Key=exp_prefix,Value={exp_prefix} --region {aws_region}
        """.format(exp_prefix=exp_prefix, aws_region=self.region))
        sio.write("service docker start\n")
        sio.write("docker --config /home/ubuntu/.docker pull {docker_image}\n".format(docker_image=self.docker_image))
        sio.write("export AWS_DEFAULT_REGION={aws_region}\n".format(aws_region=self.region))
        sio.write("""
            curl "https://s3.amazonaws.com/aws-cli/awscli-bundle.zip" -o "awscli-bundle.zip"
            unzip awscli-bundle.zip
            sudo ./awscli-bundle/install -i /usr/local/aws -b /usr/local/bin/aws
        """)

        mnt_args = ''
        py_path = []
        output_mounts = []
        for mount in mount_points:
            if isinstance(mount, MountLocal):  # TODO: these should be mount_s3 objects
                if mount.read_only:
                    with mount.gzip() as gzip_file:
                        s3_path = self.s3_upload(os.path.realpath(gzip_file))
                        remote_tar_name = '/tmp/'+os.path.basename(gzip_file)
                        remote_unpack_name = '/tmp/'+os.path.splitext(os.path.basename(gzip_file))[0]
                    sio.write("aws s3 cp {s3_path} {remote_tar_name}\n".format(s3_path=s3_path, remote_tar_name=remote_tar_name))
                    sio.write("mkdir -p {local_code_path}\n".format(local_code_path=remote_unpack_name))
                    sio.write("tar -xvf {remote_tar_name} -C {local_code_path}\n".format(
                        local_code_path='/tmp/', 
                        remote_tar_name=remote_tar_name))
                    mount_point =  os.path.join('/mounts', mount.mount_point.replace('~/',''))
                    mnt_args += ' -v %s:%s' % (remote_unpack_name, mount_point)
                    if mount.pythonpath:
                        py_path.append(mount_point)
                else:
                    raise ValueError()
            elif isinstance(mount, MountS3):
                remote_dir = mount.mount_point
                s3_path = os.path.join(remote_log_dir, mount.s3_path)
                sio.write("mkdir -p {remote_dir}\n".format(remote_dir=remote_dir))
                mnt_args += ' -v %s:%s' % (remote_dir, mount.mount_point)

                # Sync interval
                sio.write("""
                while /bin/true; do
                    aws s3 sync --exclude '*' --include '*.txt' --include '*.log' --include '*.csv' --include '*.json' {log_dir} {s3_path}
                    sleep {periodic_sync_interval}
                done & echo sync initiated""".format( log_dir=remote_dir, s3_path=s3_path,
                                                     periodic_sync_interval=mount.sync_interval))
                # Sync on terminate
                sio.write("""
                    while /bin/true; do
                        if [ -z $(curl -Is http://169.254.169.254/latest/meta-data/spot/termination-time | head -1 | grep 404 | cut -d \  -f 2) ]
                          then
                            logger "Running shutdown hook."
                            aws s3 cp --recursive {log_dir} {s3_path}
                            break
                          else
                            # Spot instance not yet marked for termination.
                            sleep 5
                        fi
                    done & echo log sync initiated
                """.format(log_dir=remote_dir, s3_path=s3_path))
            else:
                raise NotImplementedError()


        sio.write("aws ec2 create-tags --resources $EC2_INSTANCE_ID --tags Key=Name,Value={exp_name} --region {aws_region}\n".format(
            exp_name=exp_name, aws_region=self.region))
        sio.write("mkdir -p {log_dir}\n".format(log_dir=log_dir))
        docker_cmd = self.get_docker_cmd(main_cmd, use_tty=False, extra_args=mnt_args, pythonpath=py_path)
        sio.write(docker_cmd+'\n')

        sio.write("aws s3 cp --recursive {log_dir} {remote_log_dir}\n".format(log_dir=log_dir, remote_log_dir=remote_log_dir))
        sio.write("aws s3 cp /home/ubuntu/user_data.log {remote_log_dir}/stdout.log\n".format(remote_log_dir=remote_log_dir))

        if self.terminate:
            sio.write("""
                EC2_INSTANCE_ID="`wget -q -O - http://169.254.169.254/latest/meta-data/instance-id || die \"wget instance-id has failed: $?\"`"
                aws ec2 terminate-instances --instance-ids $EC2_INSTANCE_ID --region {aws_region}
            """.format(aws_region=self.region))
        sio.write("} >> /home/ubuntu/user_data.log 2>&1\n")

        full_script = dedent(sio.getvalue())
        import boto3
        ec2 = boto3.client(
            "ec2",
            region_name=self.region,
            aws_access_key_id=self.credentials.aws_key,
            aws_secret_access_key=self.credentials.aws_secret_key,
        )

        if len(full_script) > 10000 or len(base64.b64encode(full_script.encode()).decode("utf-8")) > 10000:
            s3_path = self.upload_file_to_s3(full_script, dry=dry)
            sio = StringIO()
            sio.write("#!/bin/bash\n")
            sio.write("""
            aws s3 cp {s3_path} /home/ubuntu/remote_script.sh --region {aws_region} && \\
            chmod +x /home/ubuntu/remote_script.sh && \\
            bash /home/ubuntu/remote_script.sh
            """.format(s3_path=s3_path, aws_region=self.region))
            user_data = dedent(sio.getvalue())
        else:
            user_data = full_script

        print(full_script)
        #with open("/tmp/full_script", "w") as f:
        #    f.write(full_script)

        instance_args = dict(
            ImageId=aws_config["image_id"],
            KeyName=aws_config["key_name"],
            UserData=user_data,
            InstanceType=aws_config["instance_type"],
            EbsOptimized=False,
            SecurityGroups=aws_config["security_groups"],
            SecurityGroupIds=aws_config["security_group_ids"],
            NetworkInterfaces=aws_config["network_interfaces"],
            IamInstanceProfile=dict(
                Name=aws_config["iam_instance_profile_name"],
            ),
            #**config.AWS_EXTRA_CONFIGS,
        )

        print("************************************************************")
        print('UserData:', instance_args["UserData"])
        print("************************************************************")
        instance_args["UserData"] = base64.b64encode(instance_args["UserData"].encode()).decode("utf-8")
        spot_args = dict(
            DryRun=dry,
            InstanceCount=1,
            LaunchSpecification=instance_args,
            SpotPrice=aws_config["spot_price"],
            # ClientToken=params_list[0]["exp_name"],
        )
        import pprint
        pprint.pprint(spot_args)
        if not dry:
            response = ec2.request_spot_instances(**spot_args)
            print(response)
            spot_request_id = response['SpotInstanceRequests'][
                0]['SpotInstanceRequestId']
            for _ in range(10):
                try:
                    ec2.create_tags(
                        Resources=[spot_request_id],
                        Tags=[
                            {'Key': 'Name', 'Value': exp_name}
                        ],
                    )
                    break
                except botocore.exceptions.ClientError:
                    continue


class CodalabDocker(DockerMode):
    def __init__(self):
        super(CodalabDocker, self).__init__()
        raise NotImplementedError()

