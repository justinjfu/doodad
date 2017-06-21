import pickle
import base64
import argparse
import os

ARGS_DATA = 'DOODAD_ARGS_DATA'
USE_CLOUDPICKLE = 'DOODAD_USE_CLOUDPICLE'


__ARGS = None
def __get_arg_config():
    """
    global __ARGS
    if __ARGS is not None:
        return __ARGS
    #TODO: use environment variables rather than command-line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--use_cloudpickle', type=bool, default=False)
    parser.add_argument('--'+ARGS_DATA, type=str, default='')
    parser.add_argument('--output_dir', type=str, default='/tmp/expt/')
    args = parser.parse_args()
    __ARGS = args
    """
    args_data = os.environ.get(ARGS_DATA, {})
    use_cloudpickle = os.environ.get(USE_CLOUDPICKLE, False)

    args = lambda : None # hack - use function as namespace
    args.args_data = args_data
    args.use_cloudpickle = use_cloudpickle
    return args


def get_args(key=None, default=None):
    args = __get_arg_config()

    if args.args_data:
        if args.use_cloudpickle:
            import cloudpickle
            data = cloudpickle.loads(base64.b64decode(args.args_data))
        else:
            data = pickle.loads(base64.b64decode(args.args_data))
    else:
        data = {}

    if key is not None:
        return data.get(key, default)
    return data

def encode_args(call_args, cloudpickle=False):
    """
    Encode call_args dictionary as a base64 string
    """
    assert isinstance(call_args, dict)

    if cloudpickle:
        import cloudpickle
        data = base64.b64encode(cloudpickle.dumps(call_args)).decode("utf-8")
    else:
        data = base64.b64encode(pickle.dumps(call_args)).decode("utf-8")
    return data
