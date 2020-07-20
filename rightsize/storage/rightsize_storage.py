

class RightsizeStorage:
    @property
    def image_name(self):
        raise NotImplementedError('You must override this method')

    @property
    def storage(self):
        if not self._storage:
            self.attach()
        return self._storage

    @property
    def flow(self):
        return self._flow

    def __init__(self, flow: 'rightsize.distributed.flow.RightsizeFlow'):
        self._flow = flow
        self._storage = None

    def attach(self):
        raise NotImplementedError('You must override this method')

    @classmethod
    def create(cls, *args, storage_provider: str):
        # TODO - this should be a dynamic discovery
        from rightsize.storage.rightsize_storage_docker import RightsizeStorageDocker
        from rightsize.storage.rightsize_storage_s3 import RightsizeStorageS3
        storage_class_map = {
            'RightsizeStorageDocker': RightsizeStorageDocker,
            'RightsizeStorageS3': RightsizeStorageS3
        }
        return storage_class_map[storage_provider](*args)
