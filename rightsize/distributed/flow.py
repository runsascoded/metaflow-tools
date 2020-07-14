import base64
import os
import re

import boto3
import prefect
from ctxcommon.util.aws_utils import DEFAULT_REGION
from dask_cloudprovider.providers.aws.ecs import FargateCluster
from prefect import Flow
from prefect.engine.executors import DaskExecutor
from prefect.environments import DaskCloudProviderEnvironment
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

        # see https://docs.prefect.io/api/latest/environments/execution.html#daskcloudproviderenvironment
        # Args:
        # provider_class (class): Class of a provider from the Dask Cloud Provider projects. Current supported options are ECSCluster and FargateCluster.
        # adaptive_min_workers (int, optional): Minimum number of workers for adaptive mode. If this value is None, then adaptive mode will not be used and you should pass n_workers or the appropriate kwarg for the provider class you are using.
        # adaptive_max_workers (int, optional): Maximum number of workers for adaptive mode.
        # security (Type[Security], optional): a Dask Security object from distributed.security.Security. Use this to connect to a Dask cluster that is enabled with TLS encryption. For more on using TLS with Dask see https://distributed.dask.org/en/latest/tls.html
        # executor_kwargs (dict, optional): a dictionary of kwargs to be passed to the executor; defaults to an empty dictionary
        # labels (List[str], optional): a list of labels, which are arbitrary string identifiers used by Prefect Agents when polling for work
        # on_execute (Callable[[Dict[str, Any], Dict[str, Any]], None], optional): a function callback which will be called before the flow begins to run. The callback function can examine the Flow run parameters and modify kwargs to be passed to the Dask Cloud Provider class's constructor prior to launching the Dask cluster for the Flow run. This allows for dynamically sizing the cluster based on the Flow run parameters, e.g. settings n_workers. The callback function's signature should be: on_execute(parameters: Dict[str, Any], provider_kwargs: Dict[str, Any]) -> None The callback function may modify provider_kwargs (e.g. provider_kwargs["n_workers"] = 3) and any relevant changes will be used when creating the Dask cluster via a Dask Cloud Provider class.
        # on_start (Callable, optional): a function callback which will be called before the flow begins to run
        # on_exit (Callable, optional): a function callback which will be called after the flow finishes its run
        # metadata (dict, optional): extra metadata to be set and serialized on this environment
        # **kwargs (dict, optional): additional keyword arguments to pass to boto3 for register_task_definition and run_task
        # def on_execute(parameters: dict, provider_kwargs: dict) -> None:
        #     # see rightsize-venv/lib/python3.7/site-packages/dask_cloudprovider/providers/aws/ecs.py:402
        #     # production vpc
        #     provider_kwargs["vpc"] = 'vpc-5eb4a127'
        #     # use the image we just created for this particular flow
        #     provider_kwargs["image"] = '386834949250.dkr.ecr.us-east-1.amazonaws.com/rightsize_99_standard_py37'
        #     a = 1
        #
        # environment = DaskCloudProviderEnvironment(
        #     FargateCluster,
        #     adaptive_min_workers=1,
        #     on_execute=on_execute,
        # )
        # # self.environment = environment


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
        # This creates a direct link to an existing scheduler
        # executor = DaskExecutor(address=scheduler)
        # To link to the dask_cloudprovider
        # @see https://docs.prefect.io/api/latest/engine/executors.html#daskexecutor
        def on_execute(parameters: dict, provider_kwargs: dict) -> None:
            # see rightsize-venv/lib/python3.7/site-packages/dask_cloudprovider/providers/aws/ecs.py:402
            # production vpc
            # provider_kwargs["vpc"] = 'vpc-5eb4a127'
            # use the image we just created for this particular flow
            # provider_kwargs["image"] = '386834949250.dkr.ecr.us-east-1.amazonaws.com/rightsize_99_standard_py37'
            a = 1
        # @see https://cloudprovider.dask.org/en/latest/api.html#dask_cloudprovider.ECSCluster
        executor = DaskExecutor(cluster_class='dask_cloudprovider.FargateCluster',
                                cluster_kwargs={
                                    'vpc': 'vpc-5eb4a127',
                                    # use the image we just created for this particular flow
                                    'image': '386834949250.dkr.ecr.us-east-1.amazonaws.com/rightsize_99_standard_py37',
                                    # 'adaptive_min_workers': 1,
                                    # 'on_execute': on_execute
                                }
                                )
        pass_kwargs['executor'] = executor
        try:
            return super(RightsizeFlow, self).run(**pass_kwargs)
        except Exception as ex:
            raise ex
