import itertools

class Sweeper(object):
    def __init__(self, hyper_config, repeat=1):
        self.hyper_config = hyper_config
        self.repeat = repeat

    def __iter__(self):
        count = 0
        for _ in range(self.repeat):
            for config in itertools.product(*[val for val in self.hyper_config.values()]):
                kwargs = {key:config[i] for i, key in enumerate(self.hyper_config.keys())}
                #timestamp = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
                #kwargs['exp_name'] = '%d' % count #"%s_%d" % (timestamp, count)
                count += 1
                yield kwargs

if __name__ == "__main__":
    params = {
        'a': [0,1,2],
        'b': [0,1,2],
    }

    for x in Sweeper(params):
        print(x)
