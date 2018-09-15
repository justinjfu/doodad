import tempfile

from doodad.dfile import utils

class TmpCacheFile(object):
    def __init__(self, mode):
        self.file = tempfile.mkstemp()
        if utils.is_read_mode(mode):
            self.on_load()

    def on_load(self):
        raise NotImplementedError()

    def on_flush(self):
        raise NotImplementedError()

    def __enter__(self):
        pass

    def __exit__(self):
        self.close()

    def close(self):
        self.flush()
        self.file.close()

    def flush(self):
        self.file.flush()
        self.on_flush()

    def __getattr__(self, attr):
        return getattr(self.file, attr)

