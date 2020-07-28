from rightsize.distributed.remote import rsremote

# These imports are for extra info - not strictly required
from datetime import datetime
from distributed import get_worker

###
# Sample client usage in an ad hoc function remoting, using rsremote annotations.  This sample connects to
# both CPU and GPU resources
###

print("*** Sample resremote operation invocation")


# This task will run on
@rsremote(processor_type='cpu')
def say_hello_rstask_cpu(name):
    print(f'{datetime.now()}: CPU: rstask hello {name}', flush=True)
    worker = get_worker()
    return f'Done CPU on worker {worker.name}, scheduler at {worker.scheduler.address}'


@rsremote(processor_type='gpu')
def say_hello_rstask_gpu(name):
    print(f'{datetime.now()}: GPU: rstask hello {name}', flush=True)
    worker = get_worker()
    return f'Done GPU on worker {worker.name}, scheduler at {worker.scheduler.address}'

# right now, only submit and map for client_method are supported.  We may introduce others.  For more advanced Dask
# and Distributed usage, you can access the Dask/Distributed libraries directly.
@rsremote(client_method='map', iterator=range(10))
def simple_map_increment(x):
    return x + 1


print("*** *** Using a CPU")
# With the rsremote wrapper, the function ends up as a future
cpu_func_future = say_hello_rstask_cpu('Someone trying to use a CPU')
# to get the return from the function, call .result() on the future
return_value = cpu_func_future.result()
print(f'CPU rsremote return value is {return_value}')

print("*** *** Using a GPU")
gpu_func_future = say_hello_rstask_gpu('Someone trying to use a GPU')
return_value = gpu_func_future.result()
print(f'GPU return value is {return_value}')

print("*** *** Using client method map")
map_func_future_list = simple_map_increment()
return_values = [r.result() for r in map_func_future_list]
print(f'Map return values are {return_values}')
