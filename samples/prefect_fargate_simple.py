import os
import subprocess
from datetime import datetime

import boto3
import prefect
from dask_cloudprovider.providers.aws.ecs import FargateCluster

from distributed import get_worker
from prefect import Flow, Parameter, task
from prefect.engine.executors import DaskExecutor
from prefect.engine.result_handlers import S3ResultHandler
from prefect.environments import FargateTaskEnvironment, LocalEnvironment, DaskCloudProviderEnvironment
from prefect.environments.storage import S3, Docker
from slugify import slugify

from ctxcommon.constants import AWS_ACCOUNT_NUMBER, VPCS
from ctxcommon.util.aws_utils import set_aws_credentials_env, DEFAULT_REGION, get_prod_subnets

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

cpu = 2048
memory = 8192
flow_name_slug = slugify(flow.name)

aws_ecr_repo_name = "prefect_flows"
aws_region = DEFAULT_REGION

# TODO - this should be latest - perhaps switch through flag to use env specific tag
base_image_tag = 'gdesmarais'

current_dir = os.getcwd()
while current_dir and current_dir != '/' and not os.path.isdir(os.path.join(current_dir, 'scripts')):
    current_dir = os.path.dirname(current_dir)
ecr_login = os.path.join(current_dir, 'scripts', 'ecr_login.sh')
docker_login = subprocess.check_output(ecr_login, shell=False)
ecr_client = boto3.client('ecr', region_name=aws_region)
ecr_token = ecr_client.get_authorization_token()
ecr_registry_url = ecr_token['authorizationData'][0]['proxyEndpoint']
registry_url_base = ecr_registry_url.replace('https://', '')
# flow_registry_url = os.path.join(registry_url_base, aws_ecr_repo_name)
flow_base_image_url = os.path.join(registry_url_base, f'rightsize_99_standard_py37:{base_image_tag}')

use_local_image = False
flow.storage = Docker(
    # Should this be the aws ecr name, like in 'FROM'?
    base_image=flow_base_image_url,
    image_name=aws_ecr_repo_name,
    image_tag=flow_name_slug, # possibly append environment
    local_image=use_local_image,
    registry_url=registry_url_base,
)

# These arguments are passed to the dask_cloudprovider.providers.aws.ecs.FargateCluster constructor,
# which is a thin wrapper around dask_cloudprovider.providers.aws.ecs.ECSCluster
# If the DaskExecutor cluster class is ecs instead of fargate, then params are just passed to ECSCluster
# In fact, whey don't we just make it ECSCluster directly...
task_definition_kwargs_dask = {
    'vpc': VPCS['production'],
    'fargate_use_private_ip': True,
    'cluster_name_template': f'dask-test-gdesmarais-{{uuid}}',
    # 'security_groups': [security_group],
    'execution_role_arn': 'arn:aws:iam::386834949250:role/prefect-dask-execution-role',
    'task_role_arn': 'arn:aws:iam::386834949250:role/prefect-dask-task-role',
    'worker_cpu': cpu,
    'worker_mem': memory,
    'cloudwatch_logs_group': '/prefect/task',
    'cloudwatch_logs_stream_prefix': 'dask-cluster',
    # worker_gpu: int(optional)
    'cloudwatch_logs_default_retention': 3,
    #tags: dict(optional)
    'subnets': get_prod_subnets(),
}


labels = ['fargate-task', 'fargate-size-small']

flow.environment = DaskCloudProviderEnvironment(
    provider_class=FargateCluster,
    # executor_kwargs=task_definition_kwargs_dask,
    labels=labels,
    **task_definition_kwargs_dask
)

# image_name = f'{AWS_ACCOUNT_NUMBER}.dkr.ecr.us-east-1.amazonaws.com/rightsize_99_standard_py37:gdesmarais'
# bucket = 'celsius-temp-data'
# key = 'datasciences/prefect_flows/dask_cloud_provider_test'
# flow.storage = S3(bucket, key=key)
# cluster_kwargs = {
#     'vpc': VPCS['production'],
#     'fargate_use_private_ip': True,
#     'image': image_name,
#     'cluster_name_template': f'dask-test-gdesmarais-{{uuid}}'
# }
# executor_kwargs = {'cluster_kwargs': cluster_kwargs}
#
# task_definition_kwargs_fargate = {
#     'cpu': str(cpu),
#     'memory': str(memory),
#     'family': flow_name_slug,
#     'taskDefinition': flow_name_slug,
#     'taskRoleArn': 'arn:aws:iam::386834949250:role/celsius-prefect-compose-server',
#     'executionRoleArn': 'arn:aws:iam::386834949250:role/celsius-prefect-compose-server',
#     'containerDefinitions': [{
#         'name': 'flow-container',
#         'image': image_name,
#         'cpu': cpu,
#         'memory': memory,
#         'memoryReservation': memory
#     }],
#     'networkConfiguration': {
#         'awsvpcConfiguration': {
#                 'assignPublicIp': 'DISABLED',
#                 'subnets': ['subnet-4f693443', 'subnet-a0a8539f', 'subnet-0addbba2a743cc04e']
#         }
#     }
# }
# metadata = {
#     'image': image_name
# }
# executor = DaskExecutor(cluster_class='dask_cloudprovider.FargateCluster',
#                      cluster_kwargs=cluster_kwargs)
# flow.environment = FargateTaskEnvironment(
#     executor=executor,
#     region_name=DEFAULT_REGION,
#     metadata=metadata,
#     **task_definition_kwargs_fargate
# )
# flow.environment = LocalEnvironment(executor=executor, labels=labels)

flow_id = flow.register(labels=labels)

# I'd love for the flow to be populated with more info - e.g. the version (not sure what else)
print(f'Registered flow id: {flow_id}')

# How can I invoke the flow, wait for the results, and see those results?