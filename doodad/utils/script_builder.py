import os
import stat


def add_to_script(
        cmd,
        verbose=True,
        path='/tmp/doodad_generated_script.sh',
        overwrite=False,
):
    if overwrite:
        with open(path, "w") as myfile:
            myfile.write(cmd + '\n')
        # make file executable
        st = os.stat(path)
        os.chmod(path, st.st_mode | stat.S_IEXEC)
        if verbose:
            print("Script generated:", path)
    else:
        with open(path, "a") as myfile:
            myfile.write(cmd + '\n')
        if verbose:
            print("Script updated. scp this script over:", path)

