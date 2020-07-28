import warnings
from functools import wraps

from distributed import Client
from distributed.versions import VersionMismatchWarning

from rightsize.distributed.scheduler import SchedulerResolver

# TODO - possibly tell the Dask cluster to increase the number of workers based on some metrics in the task itself, or
# some metric on the annotation
# @see KubeCluster adjust() as an example, and
# https://docs.dask.org/en/latest/setup/adaptive.html?highlight=cluster#distributed.deploy.Cluster

# boto3 issues a warning not needed
warnings.filterwarnings(
    "ignore", category=VersionMismatchWarning, message="Mismatched versions found"
)


def rsremote(*decorator_args, client_method='submit', iterator=None, **decorator_kwargs):
    """
    Wrapper for single function invocation without a workflow.
    Example:
    ```
    from distributed import get_worker
    @rsremote(processor_type='gpu', branch='feature/another_branch')
    def say_hello_rstask_gpu(name):
        print(f'{datetime.now()}: GPU: rstask hello {name}', flush=True)
        worker = get_worker()
        return f'done gpu on {worker.name}, scheduler at {worker.scheduler.address}'
    ```
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
            client_addr = SchedulerResolver.find_by_attributes(attr_set=decorator_kwargs)
            client = Client(client_addr)
            if client_method == 'submit':
                a_future = client.submit(func, *args, **kwargs)
            elif client_method == 'map':
                a_future = client.map(func, iterator)
            return a_future
        return func_wrapper
    return rstask_inner
