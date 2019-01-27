# doodad

[![Build Status](https://travis-ci.com/justinjfu/doodad.svg?branch=master)](https://travis-ci.com/justinjfu/doodad)
[![codecov](https://codecov.io/gh/justinjfu/doodad/branch/master/graph/badge.svg)](https://codecov.io/gh/justinjfu/doodad)


A library for packaging dependencies and launching scripts (with a focus on python) on different platforms using Docker.
Currently supported platforms include EC2, GCP, and remotely via SSH.

doodad is designed to be as minimally invasive in your code as possible. 

## Setup
- Install python 2 or python 3. doodad is tested to work with python2.7 and python3.6 on Unix systems.

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
```python
from doodad.launch import launch_api

launch_api.run_command(
    command='echo helloworld',
)
```
This will launch a docker container and execute the command `echo helloworld`.

Launching a python program:
```python
from doodad.launch import launch_api

launch_api.run_python(
    target='path/to/my/python/script.py',
)
```
This will launch a docker container and execute the python script.


See the [wiki](https://github.com/justinjfu/doodad/wiki/Home) and [quickstart](https://github.com/justinjfu/doodad/wiki/Quickstart) guide for more details on how to package dependencies, and run programs remotely.

## Misc

EC2 code is based on [rllab](https://github.com/rll/rllab/)'s code.
