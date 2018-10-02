from doodad.dfile import tmp_cache_file

ALLOWED_MODES = {'r', 'r+', 'w', 'w+'}

def open(filename, mode='r', **kwargs):
    if mode not in ALLOWED_MODES:
        raise NotImplementedError('S3 file mode %s not implemented' % mode)
    return S3File(filename, mode=mode)

class S3File(tmp_cache_file.TmpCacheFile):
    def __init__(self, filename, mode):
        super(S3File, self).__init__(mode=mode)
        self.filename = filename
        #TODO: parse for bucket, etc.

    def on_load(self):
        #TODO: read file from S3
        raise NotImplementedError()

    def on_flush(self):
        #TODO: write file to S3
        raise NotImplementedError()

