import prefect
from dask_cloudprovider.providers.aws.ecs import FargateCluster
from prefect import Flow
from prefect.engine.executors import DaskExecutor
from prefect.environments import DaskCloudProviderEnvironment, FargateTaskEnvironment

from rightsize.distributed.scheduler import SchedulerResolver, PREFECT_COMPOSE_HOST

# Upon loading this file, which should happen before any flows are used or interacted with, we should
# initialize the location of the prefect server.
from rightsize.storage.rightsize_storage import RightsizeStorage
from util.aws_utils import safe_cluster_name
from util.utils import get_logger

logger = get_logger()

def initialize_prefect():
    # TODO - this should be an actual endpoint
    prefect.context.config.cloud.graphql = f'http://{PREFECT_COMPOSE_HOST}:4200/graphql'
    prefect.context.config.cloud.diagnostics = True
    # prefect.context.config.cloud.api = f'http://{PREFECT_COMPOSE_HOST}:4200'
    # prefect.context.config.server.host = f'http://{PREFECT_COMPOSE_HOST}'


initialize_prefect()


class RightsizeFlow(Flow):
    storage_arg_names = {
        # 'storage_provider': 'RightsizeStorageDocker',
        'storage_provider': 'RightsizeStorageS3',
    }
    environment_arg_names = {
        'environment': 'prod'
    }
    @property
    def storage_provider(self) -> RightsizeStorage:
        return self._storage_provider

    @property
    def rs_environment(self) -> str:
        return self._rs_environment

    def __init__(self, *args, **kwargs):
        local_kwargs = kwargs.copy()
        def kw_extract(source_kwargs: dict):
            dest_kwargs = source_kwargs.copy()
            del_list = []
            for k, v in local_kwargs.items():
                if k in dest_kwargs:
                    dest_kwargs[k] = v
                    del_list.append(k)
            for d in del_list:
                del local_kwargs[d]

            return dest_kwargs


        storage_kwargs = kw_extract(self.storage_arg_names)
        logger.debug(f'extracted storage_kwargs: {storage_kwargs}')
        env_kwargs = kw_extract(self.environment_arg_names)
        logger.debug(f'extracted env_kwargs: {env_kwargs}')
        # storage_kwargs = self.storage_arg_names.copy()
        # for k, v in local_kwargs.items():
        #     if k in self.storage_arg_names:
        #         storage_kwargs[k] = v
        #         del local_kwargs[k]

        self._rs_environment = env_kwargs['environment']

        super(RightsizeFlow, self).__init__(*args, **local_kwargs)
        logger.debug(f'initialized Flow class')
        self._storage_provider = RightsizeStorage.create(self, storage_provider=storage_kwargs['storage_provider'])
        logger.debug(f'created storage provider of {self._storage_provider}')
        self.storage = self._storage_provider.storage

    def run(self, **kwargs):
        resolver_arg_names = {
            'processor_type': 'cpu',
            'branch': 'master'
        }
        # These lines are if we are hitting a dask scheduler directly, which I don't think we want
        # to do if we are using the FargateCluster approach and dynamically created dask clusters
        scheduler_kwargs = {k: v for k, v in kwargs.items() if k in resolver_arg_names}
        scheduler_addr = SchedulerResolver.find_by_attributes(scheduler_kwargs)

        pass_kwargs = {k: v for k, v in kwargs.items() if k not in resolver_arg_names}
        # we go to the storage provider in case it is a DockerStorage - but do we need to do that?  Will it always
        # be the prefect image?
        image_name = self.storage_provider.image_name
        logger.debug(f'constructed image_name of {image_name}')

        # This creates a direct link to an existing scheduler
        # executor = DaskExecutor(address=scheduler)

        # To link to the dask_cloudprovider
        # @see https://docs.prefect.io/api/latest/engine/executors.html#daskexecutor
        # @see https://cloudprovider.dask.org/en/latest/api.html#dask_cloudprovider.ECSCluster
        #             image="prefecthq/prefect:latest",
        #             task_role_arn="arn:aws:iam::<your-aws-account-number>:role/<your-aws-iam-role-name>",
        #             execution_role_arn="arn:aws:iam::<your-aws-account-number>:role/ecsTaskExecutionRole",
        #             n_workers=1,
        #             scheduler_cpu=256,
        #             scheduler_mem=512,
        #             worker_cpu=256,
        #             worker_mem=512,
        #             scheduler_timeout="15 minutes",

        ### Creating a Dask cluster in fargate
        # security_group = 'prefect-dask-sg'
        cluster_name = safe_cluster_name(self.name)
        # logger.debug(f'constructed cluster_name of {cluster_name}')
        cluster_kwargs = {
            'vpc': 'vpc-5eb4a127',
            # 'security_groups': [security_group],
            'fargate_use_private_ip': True,
            # 'execution_role_arn': 'arn:aws:iam::386834949250:role/prefect-dask-execution-role',
            # 'task_role_arn': 'arn:aws:iam::386834949250:role/prefect-dask-task-role',
            'image': image_name,
            # 'image': 'prefecthq/prefect:latest',
            'cluster_name_template': f'dask-{cluster_name}-{self.rs_environment}-{{uuid}}'
        }
        # cluster = FargateCluster(**cluster_kwargs)
        # logger.debug(f'created FargateCluster {cluster}')
        #
        # if scheduler_kwargs.get('processor_type') == 'gpu':
        #     # worker_gpu: int (optional) The number of GPUs to expose to the worker.
        #     cluster_kwargs['worker_gpu'] = 1
        # # executor = DaskExecutor(cluster_class='dask_cloudprovider.FargateCluster',
        # #                         cluster_kwargs=cluster_kwargs
        # #                         )
        # logger.debug(f'cluster scheduler is at {cluster.scheduler.address}')
        # executor = DaskExecutor(cluster.scheduler.address)
        # logger.debug(f'created DaskExecutor {executor}')
        # pass_kwargs['executor'] = executor
        ### END Creating a Dask cluster in fargate
        executor_kwargs = {'cluster_kwargs': cluster_kwargs}

        # probably not the right one
        # self.environment = DaskCloudProviderEnvironment(
        #     provider_class=FargateCluster,
        #     executor_kwargs=executor_kwargs
        # )
        # , adaptive_min_workers=None, adaptive_max_workers=None,
        # security=None, executor_kwargs=None, labels=None,
        # on_execute=None, on_start=None, on_exit=None, metadata=None, ** kwargs)
        executor = DaskExecutor(cluster_class='dask_cloudprovider.FargateCluster',
                                cluster_kwargs=cluster_kwargs)
        self.environment = FargateTaskEnvironment(
            executor=executor,
            executor_kwargs=executor_kwargs
        )
        # launch_type="FARGATE", aws_access_key_id=None, aws_secret_access_key=None, aws_session_token=None,
        # region_name=None, executor=None, executor_kwargs=None, labels=None,
        # on_start=None, on_exit=None, metadata=None, ** kwargs)
        try:
            logger.debug(f'registering Flow run')
            ret = super(RightsizeFlow, self).register()
            logger.debug(f'executing Flow run with kw_args {pass_kwargs}')
            return super(RightsizeFlow, self).run(**pass_kwargs)
        except Exception as ex:
            raise ex

