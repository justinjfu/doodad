#!/bin/bash

install_docker() {
    sudo apt-get install --no-install-recommends \
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

truncate -s 0 /home/ubuntu/user_data.log
{
    bucket_name=$(curl http://metadata/computeMetadata/v1/instance/attributes/bucket_name -H "Metadata-Flavor: Google")
    docker_image=$(curl http://metadata/computeMetadata/v1/instance/attributes/docker_image -H "Metadata-Flavor: Google")
    local_mounts=$(curl http://metadata/computeMetadata/v1/instance/attributes/local_mounts -H "Metadata-Flavor: Google")
    gce_mounts=$(curl http://metadata/computeMetadata/v1/instance/attributes/gce_mounts -H "Metadata-Flavor: Google")
    use_gpu=$(curl http://metadata/computeMetadata/v1/instance/attributes/use_gpu -H "Metadata-Flavor: Google")

    yes | sudo apt-get update
    install_docker
    sudo apt-get install jq git unzip
    die() { status=$1; shift; echo "FATAL: $*"; exit $status; }
    service docker start
    docker --config /home/ubuntu/.docker pull $docker_image

    num_local_mounts=$(jq length <<< $local_mounts)
    for ((i=0;i<$num_local_mounts;i++)); do
        local_mount=$(jq .[$i] <<< $local_mounts)
        echo "Mounting " $local_mount
        gsutil cp gs://$bucket_name/doodad/mount/$local_mount.tar /tmp/$local_mount.tar
        mkdir -p /tmp/$local_mount
        tar -xvf /tmp/$local_mount.tar -C /tmp/$local_mount
    done

    num_gce_mounts=$(jq length <<< $gce_mounts)
    for ((i=0;i<$num_gce_mounts;i++)); do
        gce_mount_info=$(jq .[$i] <<< $gce_mounts)
        # assume gce_mount_info is a (local_path, bucket_path) pair
        local_path=$(jq .[0] <<< $gce_mount_info)
        gce_bucket_path=$(jq .[1] <<< $gce_mount_info)
        echo "Adding periodic sync " $gce_mount
    done

    echo $num_mounts
} >> /home/ubuntu/user_data.log 2>&1
