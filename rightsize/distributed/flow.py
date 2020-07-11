import base64
import os
import re

import boto3
import prefect
from ctxcommon.util.aws_utils import DEFAULT_REGION
from prefect import Flow
from prefect.engine.executors import DaskExecutor
from prefect.environments.storage import Docker
from prefect.tasks.secrets import PrefectSecret
from prefect.tasks.shell import ShellTask

from rightsize.distributed.scheduler import SchedulerResolver

# Upon loading this file, which should happen before any flows are used or interacted with, we should
# initialize the location of the prefect server.
def initialize_prefect():
    # TODO - this should be an actual endpoint
    prefect.context.config.cloud.graphql = 'http://localhost:4200/graphql'


initialize_prefect()


class RightsizeFlow(Flow):
    def __init__(self, *args, **kwargs):
        super(RightsizeFlow, self).__init__(*args, **kwargs)

        ############## Storage ecr docker flow ##############
        # aws configuration
        aws_ecr_repo_name = "prefect_flows"
        aws_region = DEFAULT_REGION
        # See https://github.com/awslabs/amazon-ecr-credential-helper

        # 1. Reset Auth (hackish)
        # dkr_ecr_scrt = PrefectSecret("docker_ecr_login").run()

        # get_ecr_auth_token = ShellTask(helper_script="cd ~")
        # ecr_auth_token = get_ecr_auth_token.run(command=dkr_ecr_scrt)

        ecr_client = boto3.client('ecr', region_name=aws_region)
        ecr_token = ecr_client.get_authorization_token()

        # # Decode the aws token
        username, password = base64.b64decode(ecr_token['authorizationData'][0]['authorizationToken'])\
            .decode().split(':')
        ecr_registry_url = ecr_token['authorizationData'][0]['proxyEndpoint']

        # # Registry URL for prefect or docker push
        flow_registry_url = os.path.join(ecr_registry_url.replace('https://', ''), aws_ecr_repo_name)

        # see https://docs.prefect.io/api/latest/environments/storage.html#docker
        image_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', self.name).lower()
        # docker tag prefect_flows:latest 386834949250.dkr.ecr.us-east-1.amazonaws.com/prefect_flows:latest
        # registry_url = "386834949250.dkr.ecr.us-east-1.amazonaws.com/prefect_flows"

        # local_image (bool, optional): an optional flag whether or not to use a local docker image,
        # if True then a pull will not be attempted
        use_local_image = True

        storage = Docker(
            base_image='celsiustx/rightsize_99_standard_py37',
            image_name=image_name,
            local_image=use_local_image,
            # registry_url=flow_registry_url
        )
        self.storage = storage


    def run(self, **kwargs):
        resolver_arg_names = {
            'processor_type': 'cpu',
            'branch': 'master'
        }
        scheduler_kwargs = {k: v for k, v in kwargs.items() if k in resolver_arg_names}
        scheduler = SchedulerResolver.find_by_attributes(scheduler_kwargs)


        pass_kwargs = {k: v for k, v in kwargs.items() if k not in resolver_arg_names}
        # class prefect.environments.execution.dask.cloud_provider.DaskCloudProviderEnvironment
        # (provider_class, adaptive_min_workers=None, adaptive_max_workers=None, security=None, executor_kwargs=None,
        # labels=None, on_execute=None, on_start=None, on_exit=None, metadata=None, **kwargs)
        executor = DaskExecutor(address=scheduler)
        pass_kwargs['executor'] = executor
        try:
            return super(RightsizeFlow, self).run(**pass_kwargs)
        except Exception as ex:
            raise ex
