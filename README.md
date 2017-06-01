poodag
=====

A library for launching programs on different machines. Currently supports running locally and over EC2 and SSH (via Docker).


Setup
-----
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
pip install --upgrade --user awscli
python scripts/ec2_setup.py
```

- (Optional) Set up [Docker](https://docs.docker.com/engine/installation/). This is required on the target machine if running in a Docker-enabled mode.


Example
----
See [ec2_launch_test.py](https://github.com/justinjfu/poodag/blob/master/examples/ec2_launch/ec2_launch_test.py) for an example on how to run scripts on EC2, over SSH, or locally.

TODOs
-----
- Add support for automatic experiment restarting (will require the user to write a save_state and restore_state function, or use something like CRIU)
