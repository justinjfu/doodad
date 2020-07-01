import math


class SlurmJobGenerator(object):
    def __init__(
            self,
            account_name,
            partition,
            time_in_mins,
            max_num_cores_per_node,
            n_gpus=0,
            n_cpus_per_task=1,
            n_nodes=None,
            n_tasks=1,
            extra_flags="",
    ):
        if n_gpus > 0 and n_cpus_per_task < 2:
            raise ValueError("Must have at least 2 cpus per GPU task")
        self.account_name = account_name
        self.partition = partition
        self.time_in_mins = time_in_mins
        self.n_nodes = n_nodes
        self.n_gpus = n_gpus
        self.n_cpus_per_task = n_cpus_per_task
        self.max_num_cores_per_node = max_num_cores_per_node
        self.n_tasks = n_tasks
        self.extra_flags = extra_flags

    def wrap_command_with_sbatch(self, cmd):
        cmd = cmd.replace("'", "\\'")
        num_cpus = self.n_tasks * self.n_cpus_per_task
        n_nodes = self.n_nodes or math.ceil(
            num_cpus / self.max_num_cores_per_node)
        if self.n_gpus > 0:
            full_cmd = (
                "sbatch -A {account_name} -p {partition} -t {time}"
                " -N {nodes} -n {n_tasks} --cpus-per-task={cpus_per_task}"
                " --gres=gpu:{n_gpus} {extra_flags} --wrap=$'{cmd}'".format(
                    account_name=self.account_name,
                    partition=self.partition,
                    time=self.time_in_mins,
                    nodes=n_nodes,
                    n_tasks=self.n_tasks,
                    cpus_per_task=self.n_cpus_per_task,
                    cmd=cmd,
                    n_gpus=self.n_gpus,
                    extra_flags=self.extra_flags,
                )
            )
        else:
            full_cmd = (
                "sbatch -A {account_name} -p {partition} -t {time}"
                " -N {nodes} -n {n_tasks} --cpus-per-task={cpus_per_task}"
                " {extra_flags} --wrap=$'{cmd}'".format(
                    account_name=self.account_name,
                    partition=self.partition,
                    time=self.time_in_mins,
                    nodes=n_nodes,
                    n_tasks=self.n_tasks,
                    cpus_per_task=self.n_cpus_per_task,
                    cmd=cmd,
                    extra_flags=self.extra_flags,
                )
            )
        return full_cmd

