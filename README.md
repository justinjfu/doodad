# doodad

A library for packaging dependencies and launching scripts (with a focus on python) on different platforms using Docker.
Currently supported platforms include EC2, GCP, and remotely via SSH.

doodad is designed to be as minimally invasive in your code as possible. 

## Setup
- Install [Docker CE](https://docs.docker.com/engine/installation/).

- Add this repo to your pythonpath. 
```
export PYTHONPATH=$PYTHONPATH:/path/to/this/repo
```

- Install dependencies
```
pip install -r requirements.txt
```

- (Optional) Set up EC2
```
python scripts/ec2_setup.py
```

## Tutorial
A simple hello world program:
```
from doodad.launch import launch_api, mode

launch_api.run_command(
    command='echo helloworld',
    mode=mode.LocalMode(),
)
```
This will launch a docker container and execute the command `echo helloworld`.

Launching a python program:
```
from doodad.launch import launch_api, mode

launch_api.run_python(
    target='path/to/my/python/script.py',
    mode=mode.LocalMode(),
)
```
This will launch a docker container and execute the python script.


See the [wiki](https://github.com/justinjfu/doodad/wiki/Home) for more details on how to package dependencies, and run programs remotely.

## Misc

EC2 code is based on [rllab](https://github.com/rll/rllab/)'s code.
