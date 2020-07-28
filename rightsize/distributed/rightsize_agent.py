import os

# import prefect
from prefect.agent.agent import Agent

from rightsize.distributed.scheduler import PREFECT_COMPOSE_HOST

# export PREFECT__CLOUD__AGENT__LABELS="['s3-flow-storage', 'fargate-task', 'fargate-size-small']"
# export PREFECT__CLOUD__API=http://10.72.112.29:4200
# export PREFECT__CLOUD__AUTH_TOKEN
# export PREFECT__CLOUD__USE_LOCAL_SECRETS=false
# export PREFECT__CONTEXT__FLOW_ID=1603a316-8fad-4a08-bf5e-1297bda9edc8
# export PREFECT__CONTEXT__FLOW_RUN_ID=b06a03f7-4234-49c7-a585-a3c2a94f1fb2
# export PREFECT__ENGINE__FLOW_RUNNER__DEFAULT_CLASS=prefect.engine.cloud.CloudFlowRunner
# export PREFECT__ENGINE__TASK_RUNNER__DEFAULT_CLASS=prefect.engine.cloud.CloudTaskRunner
# export PREFECT__LOGGING__LEVEL=DEBUG
# export PREFECT__LOGGING__LOG_TO_CLOUD=true
# prefect.context.config.cloud.graphql = f'http://{PREFECT_COMPOSE_HOST}:4200/graphql'
os.environ['PREFECT__CLOUD__GRAPHQL'] = f'http://{PREFECT_COMPOSE_HOST}:4200/graphql'
# prefect.context.config.cloud.api = f'http://{PREFECT_COMPOSE_HOST}:4200'
os.environ['PREFECT__CLOUD__API'] = f'http://{PREFECT_COMPOSE_HOST}:4200'
# prefect.context.config.backend = 'server'
os.environ['PREFECT__BACKEND'] = 'server'

labels = ['s3-flow-storage']
agent = Agent(labels=labels)


agent.start()
