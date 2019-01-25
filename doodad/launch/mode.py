
class LaunchMode(object):
    def __init__(self):
        pass

    def run_script(self, script_filename):
        """
        Runs a shell script.
        """
        raise NotImplementedError()

class LocalMode(LaunchMode):
    def __init__(self):
        pass

    def run_script(self, script_filename):
        # subprocess
