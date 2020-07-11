from functools import wraps

from distributed import Client

from rightsize.distributed.scheduler import SchedulerResolver


def rsremote(*decorator_args, **decorator_kwargs):
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
            a_future = client.submit(func, *args, **kwargs)
            return a_future
        return func_wrapper
    return rstask_inner
