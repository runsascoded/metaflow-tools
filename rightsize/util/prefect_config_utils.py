def sample_server_config(self):
    """I just needed a place to hold this for a bit"""
    prefect_server_config = {
        'debug': False,
        'home_dir': '/home/ec2-user/.prefect',
        'backend': 'cloud',
        'server': {
            'host': 'http://localhost',
            'port': 4200,
            'host_port': 4200,
            'endpoint': 'http://localhost:4200',
            'database': {
                'host': 'localhost',
                'port': 5432,
                'host_port': 5432,
                'name': 'prefect_server',
                'username': 'prefect',
                'password': 'test-password',
                'connection_url': 'postgresql://prefect:test-password@localhost:5432/prefect_server',
                'volume_path': '/home/ec2-user/.prefect/pg_data'
            },
            'graphql': {
                'host': '0.0.0.0',
                'port': 4201,
                'host_port': 4201,
                'debug': False,
                'path': '/graphql/'
            },
            'hasura': {
                'host': 'localhost',
                'port': 3000,
                'host_port': 3000,
                'admin_secret': '',
                'claims_namespace': 'hasura-claims',
                'graphql_url': 'http://localhost:3000/v1alpha1/graphql',
                'ws_url': 'ws://localhost:3000/v1alpha1/graphql',
                'execute_retry_seconds': 10
            },
            'ui': {
                'host': 'http://localhost',
                'port': 8080,
                'host_port': 8080,
                'endpoint': 'http://localhost:8080',
                'graphql_url': 'http://10.72.112.29:4200/graphql'
            },
            'telemetry': {
                'enabled': True
            }
        },
        'cloud': {
            'api': 'https://api.prefect.io',
            'endpoint': 'https://api.prefect.io',
            'graphql': 'https://api.prefect.io/graphql',
            'use_local_secrets': True,
            'heartbeat_interval': 30.0,
            'diagnostics': False,
            'logging_heartbeat': 5,
            'queue_interval': 30.0,
            'agent': {
                'name': 'agent',
                'labels': [],
                'level': 'INFO',
                'auth_token': '',
                'agent_address': '',
                'resource_manager': {
                    'loop_interval': 60
                }
            }
        },
        'logging': {
            'level': 'INFO',
            'format': '[%(asctime)s] %(levelname)s - %(name)s | %(message)s',
            'log_attributes': [],
            'datefmt': '%Y-%m-%d %H:%M:%S',
            'log_to_cloud': False,
            'extra_loggers': []
        },
        'flows': {
            'eager_edge_validation': False,
            'run_on_schedule': True,
            'checkpointing': False,
            'defaults': {
                'storage': {
                    'add_default_labels': True,
                    'default_class': 'prefect.environments.storage.Local'
                }
            }
        },
        'tasks': {
            'defaults': {
                'max_retries': 0,
                'retry_delay': None,
                'timeout': None
            }
        },
        'engine': {
            'executor': {
                'default_class': 'prefect.engine.executors.LocalExecutor',
                'dask': {
                    'address': '',
                    'cluster_class': 'distributed.deploy.local.LocalCluster'
                }
            },
            'flow_runner': {
                'default_class': 'prefect.engine.flow_runner.FlowRunner'
            },
            'task_runner': {
                'default_class': 'prefect.engine.task_runner.TaskRunner'
            }
        }
    }

