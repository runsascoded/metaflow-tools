import time

import prefect

from prefect import Flow, task, Client
from prefect.engine.executors import DaskExecutor, LocalDaskExecutor
from prefect.environments import LocalEnvironment
from prefect.environments.storage import S3
from rightsize.distributed.scheduler import PREFECT_COMPOSE_HOST

# set_aws_credentials_env()
prefect.context.config.cloud.graphql = 'http://10.72.112.29:4200/graphql'

@task(log_stdout=True)
def say_hello():
    return f'done'

with Flow("Dask ECS Test 2") as flow:
    say_hello()

bucket = 'celsius-temp-data'
key = 'datasciences/prefect_flows/dask_ecs_flow_test_2'
flow.storage = S3(bucket, key=key)
# image_name = f'{AWS_ACCOUNT_NUMBER}.dkr.ecr.us-east-1.amazonaws.com/rightsize_99_standard_py37:gdesmarais'
# cluster_kwargs = {
#     'vpc': VPCS['production'],
#     'fargate_use_private_ip': True,
#     'image': image_name,
#     'cluster_name_template': f'dask-test-gdesmarais-{{uuid}}'
# }
# executor_kwargs = {'cluster_kwargs': cluster_kwargs}
#
# task_definition_kwargs = {
#     'memoryReservation': 8192,
#     'memory': 8192,
# }

labels = ['fargate-task', 'fargate-size-small']

executor = DaskExecutor(address=f'{PREFECT_COMPOSE_HOST}:38786')
# executor = DaskExecutor(cluster_class='dask_cloudprovider.ECSCluster',
#                         cluster_kwargs=cluster_kwargs)
# flow.environment = FargateTaskEnvironment(
#     executor=executor,
#     region_name=DEFAULT_REGION,
#     **task_definition_kwargs
# )
flow.environment = LocalEnvironment(executor=executor, labels=labels)

# rv = flow.run()


flow_id = flow.register(labels=labels)

# I'd love for the flow to be populated with more info - e.g. the version (not sure what else)
print(f'Registered flow id: {flow_id}')

p_client = Client()
ret = p_client.create_flow_run(flow_id=flow_id)
print(f'Created flow run: {ret}')

# How can I invoke the flow, wait for the results, and see those results?