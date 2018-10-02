import tempfile

from doodad.dfile import utils

class TmpCacheFile(object):
    def __init__(self, mode):
        self._mode = mode
        self._tmp_file = tempfile.NamedTemporaryFile(mode=mode)
        if utils.is_read_mode(mode):
            self.on_load()
        self._dirty = False

    def on_load(self):
        raise NotImplementedError()

    def on_flush(self):
        raise NotImplementedError()

    def __enter__(self):
        self._tmp_file.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.flush()
        self._tmp_file.__exit__(exc_type, exc_val, exc_tb)

    def close(self):
        # self.flush()
        self._tmp_file.close()

    def flush(self):
        self._tmp_file.flush()
        if self._dirty:
            if utils.is_write_mode(self._mode):
                self.on_flush()
    
    def write(self, _bytes):
        self._dirty = True
        self._tmp_file.write(_bytes)

    def __getattr__(self, attr):
        return getattr(self._tmp_file, attr)

