from prefect.agent.fargate import FargateAgent

from constants import AWS_ACCOUNT_NUMBER

# see https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ecs.html#ECS.Client.register_task_definition
# for networkConfiguration and containerDefinitions
from util.aws_utils import DEFAULT_REGION

networkConfiguration = {
        'awsvpcConfiguration': {
                'assignPublicIp': 'DISABLED',
                'subnets': ['subnet-4f693443', 'subnet-a0a8539f', 'subnet-0addbba2a743cc04e']
        }
}
image_name = f'{AWS_ACCOUNT_NUMBER}.dkr.ecr.us-east-1.amazonaws.com/rightsize_99_standard_py37:gdesmarais'
cpu = '2048'
memory = '8192'
containerDefinitions = [{
    'name': 'my_container_name_from_agent',
    'image': image_name,
    'cpu': cpu,
    'memory': memory,
    'memoryReservation': 8192,
    'logConfiguration': {
        'logDriver': 'awslogs',
        'options': {
            'awslogs-region': DEFAULT_REGION,
            'awslogs-group': '/prefect/task',
            'awslogs-stream-prefix': 'task-runner-'

        }
    }
    # 'volumes': set up efs links here
}]

labels = ['s3-flow-storage', 'fargate-task', 'fargate-size-small']

agent = FargateAgent(
    # aws_access_key_id="MY_ACCESS",
    # aws_secret_access_key="MY_SECRET",
    # aws_session_token="MY_SESSION",
    region_name="us-east-1",
    networkConfiguration=networkConfiguration,
    containerDefinitions=containerDefinitions,
    cpu=cpu,
    memory=memory,
    cluster="prefect-dask-cluster-small-gdesmarais",
    labels=labels,
    executionRoleArn='arn:aws:iam::386834949250:role/celsius-prefect-compose-server',
    enable_task_revisions=True,
)

agent.start()