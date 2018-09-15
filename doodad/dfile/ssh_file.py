from doodad.dfile import tmp_cache_file

def open_ssh_file(filepath, user, host, mode='r'):
    return SSHFile(filepath, user, host, mode=mode)

class SSHFile(tmp_cache_file.TmpCacheFile):
    def __init__(self, filename, user, host, mode):
        super(SSHFile, self).__init__(mode=mode)
        self.filename = filename
        self.username = user
        self.hostname = host

    def on_load(self):
        #TODO: read file from S3
        raise NotImplementedError()

    def on_flush(self):
        #TODO: write file to S3
        raise NotImplementedError()

