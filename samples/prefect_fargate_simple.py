from datetime import datetime

import prefect

from distributed import get_worker
from prefect import Flow, Parameter, task
from prefect.engine.executors import DaskExecutor
from prefect.environments import FargateTaskEnvironment
from prefect.environments.storage import S3

from constants import AWS_ACCOUNT_NUMBER, VPCS
from util.aws_utils import set_aws_credentials_env, DEFAULT_REGION

set_aws_credentials_env()
prefect.context.config.cloud.graphql = 'http://10.72.112.29:4200/graphql'

@task(log_stdout=True)
def say_hello(t_name):
    print(f'{datetime.now()}: workflow hello {t_name}', flush=True)
    worker = get_worker()
    return f'done on {worker.name}, scheduler at {worker.scheduler.address}'


name_p = Parameter('name')
with Flow("Dask Cloud Provider Test") as flow:
    for i in range(1):
        say_hello(name_p)

bucket = 'celsius-temp-data'
key = 'datasciences/prefect_flows/dask_cloud_provider_test'
flow.storage = S3(bucket, key=key)
image_name = f'{AWS_ACCOUNT_NUMBER}.dkr.ecr.us-east-1.amazonaws.com/rightsize_99_standard_py37:gdesmarais'
cluster_kwargs = {
    'vpc': VPCS['production'],
    'fargate_use_private_ip': True,
    'image': image_name,
    'cluster_name_template': f'dask-test-gdesmarais-{{uuid}}'
}
executor_kwargs = {'cluster_kwargs': cluster_kwargs}

task_definition_kwargs = {
    'memoryReservation': 8192,
    'memory': 8192,
}

executor = DaskExecutor(cluster_class='dask_cloudprovider.FargateCluster',
                        cluster_kwargs=cluster_kwargs)
flow.environment = FargateTaskEnvironment(
    executor=executor,
    region_name=DEFAULT_REGION,
    **task_definition_kwargs
)

flow_id = flow.register(labels=['fargate-task'])

# I'd love for the flow to be populated with more info - e.g. the version (not sure what else)
print(f'Registered flow id: {flow_id}')

# How can I invoke the flow, wait for the results, and see those results?