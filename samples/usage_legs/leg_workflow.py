import subprocess
import time

from prefect import task

# These imports are for extra info - not strictly required
from datetime import datetime
from distributed import get_worker

from ctxcommon.data.celsius_data_objects import CountDataObject
from rightsize.distributed.flow import RightsizeFlow


@task(log_stdout=True)
def say_hello(name):
    print(f'{datetime.now()}: hello {name}', flush=True)
    worker = get_worker()
    return f'said hello to {name}, done on {worker.name}, scheduler at {worker.scheduler.address}'


@task(log_stdout=True)
def what_he_said(what_was_said):
    print('sleeping for 5 seconds')
    time.sleep(5)
    print(f'{datetime.now()}: what was said was: "{what_was_said}"', flush=True)
    worker = get_worker()
    return f'repeated what was said ({what_was_said}), done on {worker.name}, scheduler at {worker.scheduler.address}'


@task(log_stdout=True)
def show_nvidia():
    print('running nvidia-smi')
    smi = 'No nvidia information available'
    try:
        smi = subprocess.check_output(['nvidia-smi']).decode('UTF-8')
    except:
        pass
    print(f'nvidia-smi info:\n{smi}')
    return smi


@task(log_stdout=True)
def pull_small_file():
    sample = 'CID004443-1'
    cdo = CountDataObject(sample)
    file_path = cdo.download_results_data('metrics_summary.csv')
    first_ten = 'Failure!!!'
    try:
        with open(file_path, 'r') as f:
            first_ten = f.read(10)
        print(f'read {first_ten}')
    except:
        print("Oh crap, can't pull the file!")
    return first_ten


with RightsizeFlow("Simple workflow hello") as flow:
    task_what_was_said = say_hello('Greg')
    task_what_he_said = what_he_said(task_what_was_said)
    show_nvidia()
    pull_small_file()


rs_params = {'processor_type': 'cpu', 'async': False}
rs_results = flow.run(name='world of CPUs', **rs_params)
# It is safe to join here - the run call returns when the tasks are done
rs_results.join()
if rs_results.is_successful:
    result_values = rs_results.result_values
    print(f'*** *** Using a CPU: Result values are {result_values}')
    print(f'*** *** Using a CPU: Result value for say_hello is {result_values["say_hello"]}')
    print(f'*** *** Using a CPU: Result value for what_he_said is {result_values["what_he_said"]}')
    print(f'*** *** Using a CPU: Result value for show_nvidia is {result_values["show_nvidia"]}')
    print(f'*** *** Using a CPU: Result value for pull_small_file is {result_values["pull_small_file"]}')

rs_params = {'processor_type': 'gpu', 'async': True}
rs_results = flow.run(name='world of GPUs', **rs_params)

# Since our task has a sleep, this should not be ready
ready = rs_results.results_ready
# Since our task has a sleep, this should not be successful yet
success = rs_results.is_successful
# Since our task has a sleep, this should not be filled in yet
result_values = rs_results.result_values

rs_results.join()
if rs_results.results_ready and rs_results.is_successful:
    result_values = rs_results.result_values
    print(f'*** *** Using a GPU: Result values are {result_values}')
    print(f'*** *** Using a GPU: Result value for say_hello is {result_values["say_hello"]}')
    print(f'*** *** Using a GPU: Result value for what_he_said is {result_values["what_he_said"]}')
    print(f'*** *** Using a CPU: Result value for show_nvidia is {result_values["show_nvidia"]}')
    print(f'*** *** Using a CPU: Result value for pull_small_file is {result_values["pull_small_file"]}')

