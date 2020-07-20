import re

from prefect.environments.storage import S3
from ctxcommon.util.aws_utils import set_aws_credentials_env

from rightsize.constants import DEFAULT_DOCKER_IMAGE
from rightsize.storage.rightsize_storage import RightsizeStorage

# TODO - this class is not working.  The authentication to ECR isn't triggered appropriately.


class RightsizeStorageS3(RightsizeStorage):
    key_base = 'datasciences/prefect_flows'

    @property
    def image_name(self):
        return f'{DEFAULT_DOCKER_IMAGE}:{self.flow.rs_environment}'

    def attach(self):
        set_aws_credentials_env()
        client_options = {}
        key_leaf = re.sub(r'[^a-zA-Z0-9_.-]', '_', self.flow.name).lower()
        key = '/'.join([self.key_base, key_leaf])
        self._storage = S3('celsius-temp-data', client_options=client_options, key=key)


