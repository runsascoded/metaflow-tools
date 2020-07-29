import time
import warnings

import prefect
from distributed.versions import VersionMismatchWarning
from prefect import Flow, Client
from prefect.engine.executors import DaskExecutor
from prefect.engine.results import PrefectResult
from prefect.engine.state import State
from prefect.environments import LocalEnvironment
from prefect.tasks.core.function import FunctionTask

from rightsize.distributed.scheduler import SchedulerResolver, PREFECT_COMPOSE_HOST

# Upon loading this file, which should happen before any flows are used or interacted with, we should
# initialize the location of the prefect server.
from rightsize.storage.rightsize_storage import RightsizeStorage
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

warnings.filterwarnings('ignore', category=VersionMismatchWarning, message='Mismatched versions found')


class RightsizeFlowResults:
    @property
    def results_ready(self) -> bool:
        if self._prefect_results:
            return True
        else:
            data = self._flow.p_client.get_flow_run_info(self._flow.last_flow_run_id)
            return all([tr.state.is_finished() for tr in data.task_runs])

    @property
    def is_successful(self) -> bool:
        if self._prefect_results:
            return self._prefect_results.is_successful()
        else:
            data = self._flow.p_client.get_flow_run_info(self._flow.last_flow_run_id)
            return all([tr.state.is_successful() for tr in data.task_runs])

    @property
    def result_values(self) -> dict:
        values = {}
        if self._prefect_results:
            # First, discover which names need a qualifier, if any
            qualifiers = {}
            names = []
            for result_type, result_details in self._prefect_results.result.items():
                if type(result_type) == FunctionTask:
                    nm = result_type.name
                    if nm in names:
                        qualifiers[nm] = 0
                    else:
                        names.append(nm)
            for result_type, result_details in self._prefect_results.result.items():
                if type(result_type) == FunctionTask:
                    nm = result_type.name
                    if nm in qualifiers:
                        nm += f':{qualifiers[nm]}'
                        qualifiers[result_type.name] += 1
                    values[nm] = result_details.result
        else:
            data = self._flow.p_client.get_flow_run_info(self._flow.last_flow_run_id)
            values = {self.find_name_by_slug(tr.task_slug): tr.state._result.location for tr in data.task_runs}
        return values

    def __init__(self, flow: 'RightsizeFlow', prefect_results: State = None):
        self._flow = flow
        self._prefect_results = prefect_results
        self._poll_sleep = 5

    def join(self, timeout=None):
        end_time = time() + timeout if timeout else None
        if not self._prefect_results:
            data = self._flow.p_client.get_flow_run_info(self._flow.last_flow_run_id)
            while any([not tr.state.is_finished() for tr in data.task_runs]):
                if end_time and time() > end_time:
                    return self
                time.sleep(self._poll_sleep)
                data = self._flow.p_client.get_flow_run_info(self._flow.last_flow_run_id)
        return self

    def find_name_by_slug(self, slug):
        for task in self._flow.tasks:
            if task.slug == slug:
                return task.name
        return slug


class RightsizeFlow(Flow):
    storage_arg_names = {
        # 'storage_provider': 'RightsizeStorageDocker',
        'storage_provider': 'RightsizeStorageS3',
    }
    environment_arg_names = {
        'environment': 'gdesmarais'
    }
    runtime_arg_names = {
        'async': True
    }
    resolver_arg_names = {
        'processor_type': 'cpu',
        'branch': 'prod'
    }

    @property
    def storage_provider(self) -> RightsizeStorage:
        return self._storage_provider

    @property
    def rs_environment(self) -> str:
        return self._rs_environment

    @property
    def p_client(self):
        return self._p_client

    @property
    def results(self):
        return self._results

    @property
    def last_flow_run_id(self):
        return self._last_flow_run_id

    def __init__(self, *args, **kwargs):
        local_kwargs = kwargs.copy()
        # def kw_extract(source_kwargs: dict):
        #     dest_kwargs = source_kwargs.copy()
        #     del_list = []
        #     for k, v in local_kwargs.items():
        #         if k in dest_kwargs:
        #             dest_kwargs[k] = v
        #             del_list.append(k)
        #     for d in del_list:
        #         del local_kwargs[d]
        #
        #     return dest_kwargs

        self._storage_kwargs = self._kw_extract(local_kwargs, self.storage_arg_names)
        logger.debug(f'extracted storage_kwargs: {self._storage_kwargs}')
        self._env_kwargs = self._kw_extract(local_kwargs, self.environment_arg_names)
        logger.debug(f'extracted env_kwargs: {self._env_kwargs}')


        self._rs_environment = self._env_kwargs['environment']
        self._labels = local_kwargs.get('labels')
        self._flow_id = None
        self._last_flow_run_id = None
        self._results = None
        self._p_client = Client(f'http://{PREFECT_COMPOSE_HOST}:4200/graphql')

        local_kwargs['result'] = PrefectResult()

        super(RightsizeFlow, self).__init__(*args, **local_kwargs)
        logger.debug(f'initialized Flow class')
        self._storage_provider = RightsizeStorage.create(self, storage_provider=self._storage_kwargs['storage_provider'])
        logger.debug(f'created storage provider of {self._storage_provider}')
        self.storage = self._storage_provider.storage

    def run(self, **kwargs) -> RightsizeFlowResults:
        # These lines are if we are hitting a dask scheduler directly, which I don't think we want
        # to do if we are using the FargateCluster approach and dynamically created dask clusters
        local_kwargs = kwargs.copy()

        # scheduler_kwargs = {k: v for k, v in kwargs.items() if k in self.resolver_arg_names}
        scheduler_kwargs = self._kw_extract(local_kwargs, self.resolver_arg_names)
        scheduler_addr = SchedulerResolver.find_by_attributes(attr_set=scheduler_kwargs)

        runtime_kwargs = self._kw_extract(local_kwargs, self.runtime_arg_names)
        logger.debug(f'extracted runtime_kwargs: {runtime_kwargs}')

        # pass_kwargs = {k: v for k, v in kwargs.items() if k not in self.resolver_arg_names}
        # pass_kwargs = kwargs.copy()
        # we go to the storage provider in case it is a DockerStorage - but do we need to do that?  Will it always
        # be the prefect image?
        image_name = self.storage_provider.image_name
        logger.debug(f'constructed image_name of {image_name}')

        executor = DaskExecutor(address=scheduler_addr)
        self.environment = LocalEnvironment(executor=executor, labels=self._labels)
        try:
            if runtime_kwargs.get('async', True):
                logger.debug(f'registering Flow run')
                self._flow_id = self.register(labels=self._labels)

                self._last_flow_run_id = self.p_client.create_flow_run(flow_id=self._flow_id)
                self._results = RightsizeFlowResults(self)
                print(f'Created flow run: {self._last_flow_run_id}')
            else:
                logger.debug(f'executing flow run with kw_args {local_kwargs}')
                self._flow_id = None
                if 'name' in local_kwargs:
                    del local_kwargs['name']
                p_results = super(RightsizeFlow, self).run(executor=executor, **local_kwargs)
                self._results = RightsizeFlowResults(self, prefect_results=p_results)
        except Exception as ex:
            logger.error(f'problem running the flow {self.name}: {ex}', exc_info=ex)
            raise ex

        return self.results

    def join(self):
        while not self.results.results_ready:
            time.sleep(5)
        return self.results

    @staticmethod
    def _kw_extract(extract_from: dict, source_kwargs_def: dict) -> dict:
        dest_kwargs = source_kwargs_def.copy()
        del_list = []
        for k, v in extract_from.items():
            if k in dest_kwargs:
                dest_kwargs[k] = v
                del_list.append(k)
        for d in del_list:
            del extract_from[d]
        return dest_kwargs

