PREFECT_COMPOSE_HOST = '10.72.112.29'


class SchedulerResolver:
    clients = {
        'scheduler_cpu':  {
            'addr': f'{PREFECT_COMPOSE_HOST}:18786',
            'attrs': {
                'processor_type': 'cpu',
                'branch': 'prod',
            }
        },
        # 'scheduler_gpu': {
        #     'addr': '0.0.0.0:28786',
        #     'attrs': {
        #         'processor_type': 'gpu',
        #         'branch': 'feature/another_branch',
        #     }
        # },
        'scheduler_gpu': {
            'addr': f'{PREFECT_COMPOSE_HOST}:28786',
            'attrs': {
                'processor_type': 'gpu',
                'branch': 'prod'
            }
        },
    }
    @classmethod
    def find_by_attributes(cls, attr_set: dict = {}):
        default_attr_set = {
            'branch': 'prod'
        }
        search_attr_set = {**default_attr_set, **attr_set}
        the_client = None
        for c_name, c_def in cls.clients.items():
            matches = True
            c_attrs = c_def['attrs']
            for needed_attr, needed_value in search_attr_set.items():
                if c_attrs.get(needed_attr) != needed_value:
                    matches = False
                    break
            if matches:
                the_client = c_def['addr']
                break
        if not the_client:
            raise ValueError(f'unable to find client matching needed attributes: {attr_set}')
        return the_client

    @classmethod
    def find_cpu(cls):
        return cls.find_by_attributes(attr_set={'processor_type': 'cpu'})

    @classmethod
    def find_gpu(cls):
        return cls.find_by_attributes(attr_set={'processor_type': 'gpu'})
