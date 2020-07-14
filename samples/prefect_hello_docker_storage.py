from datetime import datetime

from distributed import get_worker
from prefect import task, Parameter
from prefect.tasks.core.function import FunctionTask

from rightsize.distributed.flow import RightsizeFlow
from rightsize.distributed.remote import rsremote

###
# Sample workflow invocation with Docker storage
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
    # for i in range(10):
    for i in range(1):
            say_hello(name)

# If we want to register this flow for future use, we can do it with
flow.register()

rs_params = {'processor_type': 'cpu'}
rs_params = {}
ret = flow.run(name='world of CPUs', **rs_params)
if ret.is_successful():
    for result_type, result_details in ret.result.items():
        if type(result_type) == FunctionTask:
            print(f'*** *** Using a CPU: Result is {result_details.result}')

# rs_params = {'processor_type': 'gpu'}
# rs_params = {}
# ret = flow.run(name='world of GPUs', **rs_params)
# if ret.is_successful():
#     for result_type, result_details in ret.result.items():
#         if type(result_type) == FunctionTask:
#             print(f'*** *** Using a GPU: Result is {result_details.result}')
