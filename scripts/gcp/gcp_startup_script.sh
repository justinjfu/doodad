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
    docker_cmd=$(query_metadata docker_cmd)
    docker_image=$(query_metadata docker_image)
    local_mounts=$(query_metadata local_mounts)
    gcp_mounts=$(query_metadata gcp_mounts)
    use_gpu=$(query_metadata use_gpu)
    terminate=$(query_metadata terminate)
    instance_name=$(curl http://metadata/computeMetadata/v1/instance/name -H "Metadata-Flavor: Google")
    echo "bucket_name:" $bucket_name
    echo "docker_cmd:" $docker_cmd
    echo "docker_image:" $docker_image
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
    service docker start
    docker --config /home/ubuntu/.docker pull $docker_image

    num_local_mounts=$(jq length <<< $local_mounts)
    for ((i=0;i<$num_local_mounts;i++)); do
        local_mount=$(jq .[$i] <<< $local_mounts | tr -d '"')
        echo "Mounting " $local_mount
        gsutil cp gs://$bucket_name/doodad/mount/$local_mount.tar /tmp/$local_mount.tar
        mkdir -p /tmp/$local_mount
        tar -xvf /tmp/$local_mount.tar -C /tmp/$local_mount
    done

    num_gcp_mounts=$(jq length <<< $gcp_mounts)
    for ((i=0;i<$num_gcp_mounts;i++)); do
        gcp_mount_info=$(jq .[$i] <<< $gcp_mounts)
        # assume _mount_info is a (local_path, bucket_path, include_string, periodic_sync_interval) tuple
        local_path=$(jq .[0] <<< $gcp_mount_info | tr -d '"')
        gcp_bucket_path=$(jq .[1] <<< $gcp_mount_info | tr -d '"')
        include_string=$(jq .[2] <<< $gcp_mount_info | tr -d '"')
        periodic_sync_interval=$(jq .[3] <<< $gcp_mount_info | tr -d '"')
        while /bin/true; do
            gsutil -m rsync -r $local_path gs://$bucket_name/$gcp_bucket_path
            sleep $periodic_sync_interval
        done & echo sync from $local_path to gs://$bucket_name/$gcp_bucket_path initiated
    done
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

    echo $docker_cmd >> run_docker_command.sh
    bash run_docker_command.sh

    if [ "$terminate" = "true" ]; then
        echo "Finished experiment. Terminating"
        zone=$(curl http://metadata/computeMetadata/v1/instance/zone -H "Metadata-Flavor: Google")
        zone="${zone##*/}"
        gcloud compute instances delete $instance_name --zone $zone --quiet
    fi
} >> /home/ubuntu/user_data.log 2>&1
