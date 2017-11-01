import itertools
from random import shuffle

class Sweeper(object):
    def __init__(self, hyper_config, repeat=1, randomize=True):
        self.hyper_config = hyper_config
        self.repeat = repeat
        self.randomize = randomize

    def __determ_iter__(self):
        count = 0
        for _ in range(self.repeat):
            for config in itertools.product(*[val for val in self.hyper_config.values()]):
                kwargs = {key:config[i] for i, key in enumerate(self.hyper_config.keys())}
                #timestamp = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
                #kwargs['exp_name'] = '%d' % count #"%s_%d" % (timestamp, count)
                count += 1
                yield kwargs

    def __rand_iter__(self):
        hypers = list(self.__determ_iter__())
        shuffle(hypers)
        for hyper in hypers:
            yield hyper

    def __iter__(self):
        if self.randomize:
            return self.__rand_iter__()
        return self.__determ_iter__()
        

if __name__ == "__main__":
    params = {
        'a': [0,1,2],
        'b': [0,1,2],
    }

    for x in Sweeper(params):
        print(x)
