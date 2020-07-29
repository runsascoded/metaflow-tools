import prefect

from prefect import Flow, task, Client
from prefect.engine.executors import DaskExecutor
from prefect.engine.results import PrefectResult
from prefect.environments import LocalEnvironment
from prefect.environments.storage import S3
from rightsize.distributed.scheduler import PREFECT_COMPOSE_HOST

prefect.context.config.cloud.graphql = 'http://10.72.112.29:4200/graphql'


@task(log_stdout=True, result=PrefectResult())
def say_hello():
    return f'done'


with Flow("Dask ECS Test 2", result=PrefectResult()) as flow:
    say_hello()

bucket = 'celsius-temp-data'
key = 'datasciences/prefect_flows/dask_ecs_flow_test_2'
flow.storage = S3(bucket, key=key)
executor = DaskExecutor(address=f'{PREFECT_COMPOSE_HOST}:18786')
flow.environment = LocalEnvironment(executor=executor)
flow_id = flow.register()
# I'd love for the flow to be populated with more info - e.g. the version (not sure what else)
print(f'Registered flow id: {flow_id}')

p_client = Client()
ret = p_client.create_flow_run(flow_id=flow_id)
print(f'Created flow run: {ret}')

# How can I invoke the flow, wait for the results, and see those results?