#!/bin/bash
query_metadata() {
    attribute_name=$1
    curl http://metadata/computeMetadata/v1/instance/attributes/$attribute_name -H "Metadata-Flavor: Google"
}

{
    bucket_name=$(query_metadata bucket_name)
    shell_interpreter=$(query_metadata shell_interpreter)
    remote_script_path=$(query_metadata remote_script_path)
    use_gpu=$(query_metadata use_gpu)
    terminate=$(query_metadata terminate)
    gcp_bucket_path=$(query_metadata gcp_bucket_path)
    instance_name=$(curl http://metadata/computeMetadata/v1/instance/name -H "Metadata-Flavor: Google")
    echo "bucket_name:" $bucket_name
    echo "gcp_bucket_path:" $gcp_bucket_path
    echo "shell_interpreter:" $shell_interpreter
    echo "remote_script:" $remote_script_path
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
    echo "downloading script"
    gsutil cp gs://$bucket_name/$remote_script_path /tmp/remote_script.sh

    # sync mount
    # Because GCPMode has no idea where the mounts are (the archive has them)
    # we just make the archive store everything into /doodad
    while /bin/true; do
        gsutil -m rsync -r /doodad gs://$bucket_name/$gcp_bucket_path/logs
        sleep 15
    done & echo sync from /doodad to gs://$bucket_name/$gcp_bucket_path/logs initiated

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
