#!/bin/bash
install_docker() {
    sudo apt-get install -y --no-install-recommends \
        apt-transport-https \
        curl \
        software-properties-common
    curl -fsSL 'https://sks-keyservers.net/pks/lookup?op=get&search=0xee6d536cf7dc86e2d7d56f59a178ac6c6238f52e' | sudo apt-key add -
    sudo add-apt-repository \
       "deb https://packages.docker.com/1.12/apt/repo/ \
       ubuntu-$(lsb_release -cs) \
       main"
    sudo apt-get update
    sudo apt-get -y install docker-engine
    sudo usermod -a -G docker ubuntu
}

query_metadata() {
    attribute_name=$1
    curl http://metadata/computeMetadata/v1/instance/attributes/$attribute_name -H "Metadata-Flavor: Google"
}

{
    bucket_name=$(query_metadata bucket_name)
    shell_interpreter=$(query_metadata shell_interpreter)
    remote_script=$(query_metadata remote_script)
    use_gpu=$(query_metadata use_gpu)
    terminate=$(query_metadata terminate)
    gcp_bucket_path=$(query_metadata gcp_bucket_path)
    instance_name=$(curl http://metadata/computeMetadata/v1/instance/name -H "Metadata-Flavor: Google")
    echo "bucket_name:" $bucket_name
    echo "docker_cmd:" $docker_cmd
    echo "local_mounts:" $local_mounts
    echo "gcp_mounts:" $gcp_mounts
    echo "use_gpu:" $use_gpu
    echo "terminate:" $terminate
    echo "instance_name:" $instance_name

    sudo apt-get update
    #install_docker
    while sudo fuser /var/{lib/{dpkg,apt/lists},cache/apt/archives}/lock >/dev/null 2>&1; do
        sleep 1
    done
    sudo apt-get install -y jq git unzip
    die() { status=$1; shift; echo "FATAL: $*"; exit $status; }
    echo "starting docker!"
    systemctl status docker.socket
    #service docker start
    echo "docker started"
    # systemctl status docker.socket
    # docker --config /home/ubuntu/.docker pull $docker_image
    echo "image pulled"

    # download script
    gsutil cp gs://$bucket_name/$remote_script /tmp/remote_script.sh

    # setup GCP. Install crcmod for faster rsync
    sudo apt-get install gcc python-dev python-setuptools
    sudo pip uninstall crcmod
    sudo pip install -U crcmod

    # sync stdout
    gcp_bucket_path=${gcp_bucket_path%/}  # remove trailing slash if present
    while /bin/true; do
        gsutil cp /home/ubuntu/user_data.log gs://$bucket_name/$gcp_bucket_path/${instance_name}_stdout.log
        sleep 300
    done &

    if [ "$use_gpu" = "true" ]; then
        for i in {1..800}; do su -c "nvidia-modprobe -u -c=0" ubuntu && break || sleep 3; done
        systemctl start nvidia-docker
        echo 'Testing nvidia-smi'
        nvidia-smi
        echo 'Testing nvidia-smi inside docker'
        nvidia-docker run --rm $docker_image nvidia-smi
    fi

    #echo $run_script_cmd >> run_script_cmd.sh
    #bash run_script_cmd.sh
    $shell_interpreter /tmp/remote_script.sh

    if [ "$terminate" = "true" ]; then
        echo "Finished experiment. Terminating"
        zone=$(curl http://metadata/computeMetadata/v1/instance/zone -H "Metadata-Flavor: Google")
        zone="${zone##*/}"
        gcloud compute instances delete $instance_name --zone $zone --quiet
    fi
} >> /home/ubuntu/user_data.log 2>&1
