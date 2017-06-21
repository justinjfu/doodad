import configparser
import os

from doodad.utils import REPO_DIR

class Autoconfig(object):
    def __init__(self, filename=None):
        if filename is None:
            filename = os.path.join(REPO_DIR, 'aws_config', 'config.ini')
        config = configparser.ConfigParser()
        config.read(filename)
        self.config = config

    def s3_bucket(self):
        return self.config['default']['s3_bucket_name']

    def iam_profile_name(self):
        return self.config['default']['iam_instance_profile_name']

    def aws_security_groups(self):
        return self.config['default']['aws_security_groups']

    def aws_access_key(self):
        return self.config['default']['aws_access_key']

    def aws_access_secret(self):
        return self.config['default']['aws_access_secret']

    def aws_image_id(self, region):
        return self.config['aws_image_ids'][region]

    def aws_key_name(self, region):
        return self.config['aws_key_names'][region]

AUTOCONFIG = Autoconfig()
