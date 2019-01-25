import subprocess

def call(cmd, verbose=False, dry=False, wait=True, shell=False):
    if dry or verbose:
        print(cmd)
    if not dry:
        p = subprocess.Popen(cmd, shell=shell)
        try:
            if wait:
                p.wait()
        except KeyboardInterrupt:
            try:
                print("terminating")
                p.terminate()
            except OSError:
                print("os error!")
                pass


def call_and_get_output(cmd, shell=False, dry=False):
    if dry:
        print(cmd)
    else:
        p = subprocess.Popen(cmd, shell=shell, stdout=subprocess.PIPE)
        output, errors = p.communicate()
        return output
