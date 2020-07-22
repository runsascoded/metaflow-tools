#!/usr/bin/env bash
#Command	["/bin/sh","-c","prefect execute cloud-flow"]
#Network bindings - not configured
#Environment Variables
#Key	Value
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
#
# prefect execute cloud-flow
from prefect.cli.execute import cloud_flow
from ctxcommon.util.aws_utils import set_aws_credentials_env

set_aws_credentials_env()

cloud_flow()
