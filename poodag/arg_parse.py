import pickle
import base64
import argparse

ARGS_DATA = 'args_data'


__ARGS = None
def __get_arg_config():
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
    return args


def get_args():
    args = __get_arg_config()
    if args.use_cloudpickle:
        import cloudpickle
        data = cloudpickle.loads(base64.b64decode(args.args_data))
    else:
        data = pickle.loads(base64.b64decode(args.args_data))
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
