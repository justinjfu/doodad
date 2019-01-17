import os
import subprocess
import argparse

def aws_sync(bucket_name, gs_log_dir, target_dir, exclude='*.pkl'):
    cmd = 'gsutil -m rsync -r gs://%s/doodad/logs/%s %s' % (bucket_name, gs_log_dir, target_dir)
    subprocess.call(cmd, shell=True)

def main():

    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('log_dir', type=str, help='GS Log dir')
    parser.add_argument('-b', '--bucket', type=str, default='doodad', help='GS Bucket')
    parser.add_argument('-e', '--exclude', type=str, default='*.pkl', help='Exclude')

    args = parser.parse_args()
    s3_log_dir = args.log_dir
    os.makedirs(s3_log_dir, exist_ok=True)
    aws_sync(args.bucket, s3_log_dir, s3_log_dir, exclude=args.exclude)

if __name__ == "__main__":
    main()
