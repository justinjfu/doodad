#!/bin/bash
query_metadata() {
    attribute_name=$1
    curl http://metadata/computeMetadata/v1/instance/attributes/$attribute_name -H "Metadata-Flavor: Google"
}

bucket_name=$(query_metadata bucket_name)
gcp_bucket_path=$(query_metadata gcp_bucket_path)
instance_name=$(curl http://metadata/computeMetadata/v1/instance/name -H "Metadata-Flavor: Google")

gsutil cp -r /doodad gs://$bucket_name/$gcp_bucket_path/logs
# sync stdout
gcp_bucket_path=${gcp_bucket_path%/}  # remove trailing slash if present
gsutil cp /home/ubuntu/user_data.log gs://$bucket_name/$gcp_bucket_path/${instance_name}_stdout.log
