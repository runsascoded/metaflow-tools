from datetime import datetime
from functools import wraps

from distributed import Client, get_worker
from prefect import task, Flow, Parameter, Task
from prefect.engine.executors import DaskExecutor
from prefect.environments import LocalEnvironment

class RightsizeResolver:
    clients = {
        'client1':  {
            'addr': '0.0.0.0:18786',
            'attrs' : {
                'processor_type': 'cpu',
                'branch': 'master',
            }
        },
        'client2': {
            'addr': '0.0.0.0:28786',
            'attrs': {
                'processor_type': 'gpu',
                'branch': 'feature/another_branch',
            }
        },
    }
    @classmethod
    def find_by_attributes(cls, attr_set: dict = {}):
        default_attr_set = {
            'branch': 'master'
        }
        search_attr_set = {**default_attr_set, **attr_set}
        the_client = None
        for c_name, c_def in cls.clients.items():
            matches = True
            c_attrs = c_def['attrs']
            for needed_attr, needed_value in search_attr_set.items():
                if c_attrs.get(needed_attr) != needed_value:
                    matches = False
                    break
            if matches:
                the_client = c_def['addr']
                break
        if not the_client:
            raise ValueError(f'unable to find client matching needed attributes: {attr_set}')
        return the_client

    @classmethod
    def find_cpu(cls):
        return cls.find_by_attributes(attr_set={'processor_type': 'cpu'})

    @classmethod
    def find_gpu(cls):
        return cls.find_by_attributes(attr_set={'processor_type': 'gpu'})

# export PREFECT__ENGINE__EXECUTOR__DEFAULT_CLASS="prefect.engine.executors.DaskExecutor"
# export PREFECT__ENGINE__EXECUTOR__DASK__ADDRESS="tcp://0.0.0.0:18786"
executor = DaskExecutor(address="0.0.0.0:18786")
# class prefect.environments.execution.dask.cloud_provider.DaskCloudProviderEnvironment
# (provider_class, adaptive_min_workers=None, adaptive_max_workers=None, security=None, executor_kwargs=None,
# labels=None, on_execute=None, on_start=None, on_exit=None, metadata=None, **kwargs)

def rsremote(*decorator_args, **decorator_kwargs):
    """
    Single function invocation without a workflow.
    :param decorator_args:
    :param decorator_kwargs:
    :return:
    """

    def rstask_inner(func):
        @wraps(func)
        def func_wrapper(*args, **kwargs):
            oa = decorator_args
            okw = decorator_kwargs
            # see https://docs.dask.org/en/latest/futures.html#distributed.Client.submit
            client_addr = RightsizeResolver.find_by_attributes(attr_set=decorator_kwargs)
            client = Client(client_addr)
            a_future = client.submit(func, *args, **kwargs)
            return a_future
        return func_wrapper
    return rstask_inner

@task(log_stdout=True)
def say_hello(name):
    ret = "Hello, {}!".format(name)
    print(ret)
    return ret


@rsremote(processor_type='cpu')
def say_hello_rstask_cpu(name):
    print(f'{datetime.now()}: CPU: rstask hello {name}', flush=True)
    worker = get_worker()
    return f'done cpu on {worker.name}, scheduler at {worker.scheduler.address}'


@rsremote(processor_type='gpu', branch='feature/another_branch')
def say_hello_rstask_gpu(name):
    print(f'{datetime.now()}: GPU: rstask hello {name}', flush=True)
    worker = get_worker()
    return f'done gpu on {worker.name}, scheduler at {worker.scheduler.address}'


ret = say_hello_rstask_cpu('someone trying to use a cpu')
print(f'rstask ret is {ret}')
res = ret.result()
print(f'rstask result is {res}')

ret = say_hello_rstask_gpu('someone trying to use a gpu')
print(f'rstask ret is {ret}')
res = ret.result()
print(f'rstask result is {res}')


with Flow("My First Flow") as flow:
    name = Parameter('name')
    for i in range(10):
        # say_hello(f'{name} {i}')
        say_hello(name)

# flow.register()

a = 1
# This has to happen on a class instance, not func
# say_hello.run('singleton')


# ret = flow.run(name='world', executor=executor) # "Hello, world!"
# print(f'Returned value is {ret}')
# flow.run(name='Marvin', executor=executor) # "Hello, Marvin!"
