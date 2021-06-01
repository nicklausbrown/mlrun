import os
from . import KafkaTrigger, HttpTrigger, V3ioStreamTrigger, CronTrigger


def create_v3io_trigger(
    path,
    container: str = 'users',
    access_key: str = None,
    max_workers: int = 1,
    name: str = 'v3io-stream'
) -> V3ioStreamTrigger:

    def validate_access_key(key):
        if key is None:
            key = os.getenv('V3IO_ACCESS_KEY', None)
            if key is None:
                raise TypeError('Access Key must be declared as a parameter or in the environment as V3IO_ACCESS_KEY')
        return key

    trigger = V3ioStreamTrigger()
    trigger.attributes.stream_path = path
    trigger.attributes.container_name = container
    access_key = validate_access_key(access_key)
    trigger.add_secret(access_key)
    trigger.max_workers = max_workers
    trigger.name(name)
    return trigger


