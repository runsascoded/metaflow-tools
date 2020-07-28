from prefect import task, Parameter

# These imports are for extra info - not strictly required
from datetime import datetime
from distributed import get_worker
from prefect.engine.results import PrefectResult
from prefect.tasks.core.function import FunctionTask

from rightsize.distributed.flow import RightsizeFlow


@task(log_stdout=True, result=PrefectResult())
def say_hello(name):
    print(f'{datetime.now()}: hello {name}', flush=True)
    worker = get_worker()
    return f'said hello to {name}, done on {worker.name}, scheduler at {worker.scheduler.address}'


@task(log_stdout=True, result=PrefectResult())
def what_he_said(what_was_said):
    print(f'{datetime.now()}: what was said was: "{what_was_said}"', flush=True)
    worker = get_worker()
    return f'repeated what was said ({what_was_said}), done on {worker.name}, scheduler at {worker.scheduler.address}'


with RightsizeFlow("Simple workflow hello") as flow:
    # Since there is no return value dependency, we end up with possible parallel operations
    what_was_said = say_hello('Greg')
    flow_return = what_he_said(what_was_said)

rs_params = {'processor_type': 'cpu'}
ret = flow.run(**rs_params)
if ret.is_successful():
    for result_type, result_details in ret.result.items():
        if type(result_type) == FunctionTask:
            print(f'*** *** Using a CPU: Result is {result_details.result}')

rs_params = {'processor_type': 'gpu'}
# providing a name will register this as a flow in prefect for invocation by name later
ret = flow.run(name='world of GPUs', **rs_params)
if ret.is_successful():
    for result_type, result_details in ret.result.items():
        if type(result_type) == FunctionTask:
            print(f'*** *** Using a GPU: Result is {result_details.result}')
