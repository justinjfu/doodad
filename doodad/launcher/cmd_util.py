
class CommandBuilder(object):
    def __init__(self):
        self.cmds = []

    def append(self, cmd, args=None):
        if args:
            self.cmds.append(cmd + ' ' + args)
        else:
            self.cmds.append(cmd)


    def to_string(self, separator=';'):
        return ';'.join([str(cmd) for cmd in self])

    def __str__(self):
        return self.to_string()

    def __iter__(self):
        for cmd in self.cmds:
            if isinstance(cmd, CommandBuilder):
                for cmd_ in cmd:
                    yield cmd_
            else:
                yield cmd

    def dump_script(self):
        return '\n'.join(list(self))