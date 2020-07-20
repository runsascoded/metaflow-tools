import base64
import os
import re
import subprocess

import boto3
from prefect.environments.storage import Docker
from prefect.tasks.secrets import PrefectSecret
from prefect.tasks.shell import ShellTask

from ctxcommon.util.aws_utils import DEFAULT_REGION

from rightsize.storage.rightsize_storage import RightsizeStorage

# TODO - this class is not working.  The authentication to ECR isn't triggered appropriately.


class RightsizeStorageDocker(RightsizeStorage):
    @property
    def image_name(self):
        return re.sub(r'[^a-zA-Z0-9_.-]', '_', self.flow.name).lower()

    def attach(self):
        ############## Storage ecr docker flow ##############
        # aws configuration
        aws_ecr_repo_name = "prefect_flows"
        aws_region = DEFAULT_REGION
        # See https://github.com/awslabs/amazon-ecr-credential-helper

        # 1. Reset Auth (hackish)
        # dkr_ecr_scrt = PrefectSecret("docker_ecr_login").run()

        # get_ecr_auth_token = ShellTask(helper_script="cd ~")
        # ecr_auth_token = get_ecr_auth_token.run(command=dkr_ecr_scrt)
        # Let's determine where we are now and find the scripts directory
        current_dir = os.getcwd()
        while current_dir and current_dir != '/' and not os.path.isdir(os.path.join(current_dir, 'scripts')):
            current_dir = os.path.dirname(current_dir)
        ecr_login = os.path.join(current_dir, 'scripts', 'ecr_login.sh')
        docker_login = subprocess.check_output(ecr_login, shell=False)

        # docker_login = subprocess.check_output(f"aws ecr get-login --no-include-email --region {DEFAULT_REGION}", shell=True)
        # subprocess.check_call(docker_login) #, shell=True)
        ecr_client = boto3.client('ecr', region_name=aws_region)
        ecr_token = ecr_client.get_authorization_token()


        # # Decode the aws token
        username, password = base64.b64decode(ecr_token['authorizationData'][0]['authorizationToken'])\
            .decode().split(':')
        ecr_registry_url = ecr_token['authorizationData'][0]['proxyEndpoint']

        # # Registry URL for prefect or docker push
        flow_registry_url = os.path.join(ecr_registry_url.replace('https://', ''), aws_ecr_repo_name)

        # image_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', self.flow.name).lower()
        # docker tag prefect_flows:latest 386834949250.dkr.ecr.us-east-1.amazonaws.com/prefect_flows:latest
        # registry_url = "386834949250.dkr.ecr.us-east-1.amazonaws.com/prefect_flows"

        # local_image (bool, optional): an optional flag whether or not to use a local docker image,
        # if True then a pull will not be attempted
        use_local_image = True

        # see https://docs.prefect.io/api/latest/environments/storage.html#docker
        self._storage = Docker(
            base_image='celsiustx/rightsize_99_standard_py37',
            image_name=self.image_name,
            local_image=use_local_image,
            registry_url=flow_registry_url
        )

