import prefect
from dask_cloudprovider.providers.aws.ecs import FargateCluster
from prefect import Flow, Client
from prefect.engine import FlowRunner
from prefect.engine.executors import DaskExecutor
from prefect.engine.results import PrefectResult
from prefect.environments import DaskCloudProviderEnvironment, FargateTaskEnvironment, LocalEnvironment

from rightsize.distributed.scheduler import SchedulerResolver, PREFECT_COMPOSE_HOST

# Upon loading this file, which should happen before any flows are used or interacted with, we should
# initialize the location of the prefect server.
from rightsize.storage.rightsize_storage import RightsizeStorage
from ctxcommon.util.aws_utils import safe_cluster_name
from ctxcommon.util.utils import get_logger

logger = get_logger()

def initialize_prefect():
    # TODO - this should be an actual endpoint
    prefect.context.config.cloud.graphql = f'http://{PREFECT_COMPOSE_HOST}:4200/graphql'
    prefect.context.config.cloud.diagnostics = True
    prefect.context.config.flows.checkpointing = True
    prefect.context.config.flows.defaults.storage.default_class = 'prefect.engine.results.PrefectResult'
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
        config = prefect.context

        storage_kwargs = kw_extract(self.storage_arg_names)
        logger.debug(f'extracted storage_kwargs: {storage_kwargs}')
        env_kwargs = kw_extract(self.environment_arg_names)
        logger.debug(f'extracted env_kwargs: {env_kwargs}')

        self._rs_environment = env_kwargs['environment']
        self._labels = local_kwargs.get('labels')
        self._flow_id = None
        self._last_flow_run_id = None
        self._last_flow_run_results = None

        local_kwargs['result'] = PrefectResult()

        super(RightsizeFlow, self).__init__(*args, **local_kwargs)
        logger.debug(f'initialized Flow class')
        self._storage_provider = RightsizeStorage.create(self, storage_provider=storage_kwargs['storage_provider'])
        logger.debug(f'created storage provider of {self._storage_provider}')
        self.storage = self._storage_provider.storage


    def run(self, **kwargs):
        resolver_arg_names = {
            'processor_type': 'cpu',
            'branch': 'prod'
        }
        # These lines are if we are hitting a dask scheduler directly, which I don't think we want
        # to do if we are using the FargateCluster approach and dynamically created dask clusters
        scheduler_kwargs = {k: v for k, v in kwargs.items() if k in resolver_arg_names}
        scheduler_addr = SchedulerResolver.find_by_attributes(attr_set=scheduler_kwargs)

        pass_kwargs = {k: v for k, v in kwargs.items() if k not in resolver_arg_names}
        # we go to the storage provider in case it is a DockerStorage - but do we need to do that?  Will it always
        # be the prefect image?
        image_name = self.storage_provider.image_name
        logger.debug(f'constructed image_name of {image_name}')
        config = prefect.config
        print(config)

        executor = DaskExecutor(address=scheduler_addr)
        self.environment = LocalEnvironment(executor=executor, labels=self._labels)
        try:
            if 'name' in kwargs:
                logger.debug(f'registering Flow run')
                self._flow_id = self.register(labels=self._labels)

                p_client = Client(f'http://{PREFECT_COMPOSE_HOST}:4200/graphql')
                self._last_flow_run_id = p_client.create_flow_run(flow_id=self._flow_id)
                run_info = p_client.get_flow_run_info(self._last_flow_run_id)
                print(f'Created flow run: {self._last_flow_run_id}')
            else:
                logger.debug(f'executing flow run with kw_args {pass_kwargs}')
                self._flow_id = None
                self._last_flow_run_results = super(RightsizeFlow, self).run(executor=executor, **pass_kwargs)
        except Exception as ex:
            self._last_flow_run_results = None
            raise ex

        return self._last_flow_run_results

