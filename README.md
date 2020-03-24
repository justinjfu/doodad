# doodad

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Build Status](https://travis-ci.com/justinjfu/doodad.svg?branch=master)](https://travis-ci.com/justinjfu/doodad)
[![codecov](https://codecov.io/gh/justinjfu/doodad/branch/master/graph/badge.svg)](https://codecov.io/gh/justinjfu/doodad)

A library for packaging dependencies and launching scripts (with a focus on python) on different platforms using Docker.
Currently supported platforms include AWS, GCP, and remotely via SSH.

doodad is designed to be as minimally invasive as possible - most code can be run without any modifications.

See the [quickstart](https://github.com/justinjfu/doodad/wiki/Quickstart) guide for a quick tutorial.

## Setup
- Install Python 2.7+ or Python 3.6+. doodad currently supports both.

- Install [Docker CE](https://docs.docker.com/engine/installation/).

- Add this repo to your pythonpath. 
```
export PYTHONPATH=$PYTHONPATH:/path/to/this/repo
```

- Install dependencies
```
pip install -r requirements.txt
```

## Example
Launching commands is very simple with doodad. The following script will launch a docker container and execute the command `echo helloworld`:

```python
from doodad.launch import launch_api

launch_api.run_command('echo helloworld')
```

To launch a python program, specify the path to the script.
```python
from doodad.launch import launch_api

launch_api.run_python('path/to/my/python/script.py')
```

## Misc

EC2 code is based on [rllab](https://github.com/rll/rllab/)'s code.
