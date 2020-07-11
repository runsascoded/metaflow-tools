from datetime import datetime

from distributed import get_worker
from prefect import task, Parameter
from prefect.tasks.core.function import FunctionTask

from rightsize.distributed.flow import RightsizeFlow
from rightsize.distributed.remote import rsremote

###
# Sample invocation for a single operation - no workflow involved.
###
print("*** Sample single operation invocation")


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


print("*** *** Using a cpu")
# With the rsremote wrapper, the function ends up as a future
func_future = say_hello_rstask_cpu('someone trying to use a cpu')
# to get the return from the function, call .result() on the future
return_value = func_future.result()
print(f'return value is {return_value}')

print("*** *** Using a gpu")
func_future = say_hello_rstask_gpu('someone trying to use a gpu')
return_value = func_future.result()
print(f'return value is {return_value}')

execute_workflow = False
if not execute_workflow:
    exit(0)

###
# Sample workflow invocation
###

print("*** Sample workflow invocation")

@task(log_stdout=True)
def say_hello(name):
    print(f'{datetime.now()}: workflow hello {name}', flush=True)
    worker = get_worker()
    return f'done on {worker.name}, scheduler at {worker.scheduler.address}'


name = Parameter('name')
with RightsizeFlow("Simple parallel hello") as flow:
    # Since there is no return value dependency, we end up with possible parallel operations
    for i in range(10):
        say_hello(name)

# If we want to register this flow for future use, we can do it with
flow.register()

rs_params = {'processor_type': 'cpu'}
ret = flow.run(name='world of CPUs', **rs_params)
if ret.is_successful():
    for result_type, result_details in ret.result.items():
        if type(result_type) == FunctionTask:
            print(f'*** *** Using a CPU: Result is {result_details.result}')

rs_params = {'processor_type': 'gpu'}
ret = flow.run(name='world of GPUs', **rs_params)
if ret.is_successful():
    for result_type, result_details in ret.result.items():
        if type(result_type) == FunctionTask:
            print(f'*** *** Using a GPU: Result is {result_details.result}')
