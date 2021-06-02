import os
from typing import List, Union, Dict
from . import KafkaTrigger, HttpTrigger, V3ioStreamTrigger, CronTrigger
from .trigger import HttpIngresses


def create_v3io_trigger(
    path: str,
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


def create_kafka_trigger(
    topic: Union[str, List[str]],
    brokers: List[str],
    partitions: List[int] = None,
    consumer_group: str = 'nuclio-function',
    max_workers: int = 1,
    name: str = 'kafka-topic'
) -> KafkaTrigger:

    trigger = KafkaTrigger()
    trigger.attributes.consumer_group = consumer_group
    trigger.attributes.topics = [topic] if type(topic) is str else topic
    if partitions is None:
        partitions = [0]
    trigger.attributes.partitions = partitions
    trigger.attributes.brokers = brokers
    trigger.max_workers = max_workers
    trigger.name(name)
    return trigger


def create_http_trigger(
    port=32001,
    max_workers: int = 1,
    ingresses: Dict[str, HttpIngresses] = None,
    name: str = 'http'
) -> HttpTrigger:

    trigger = HttpTrigger()
    trigger.attributes.port = port
    if ingresses is not None:
        trigger.attributes.ingresses = ingresses
    trigger.max_workers = max_workers
    trigger.name(name)
    return trigger


def create_http_ingress(
    name: str,
    host: str,
    paths: List[str]
) -> Dict[str, HttpIngresses]:

    ingress = HttpIngresses()
    ingress.host = host
    ingress.paths = paths
    return {name: ingress}


def create_cron_trigger(
    schedule: str = None,
    interval: str = None,
    max_workers: int = 1,
    event_body: str = None,
    event_headers: Dict[str, Union[int, str]] = None,
    name: str = 'cron'
) -> CronTrigger:

    if schedule is None and interval is None:
        raise ValueError('Either schedule or interval must be specified')
    if schedule is not None and interval is not None:
        raise ValueError('Only one parameter may be specified - either schedule or interval')

    trigger = CronTrigger()
    # Nones are not serialized, so this is fine after checking above
    trigger.attributes.interval = interval
    trigger.attributes.schedule = schedule

    if event_headers is not None or event_body is not None:
        event = trigger.Attributes.Event(body=event_body, headers=event_headers)
        trigger.attributes.event = event

    trigger.max_workers = max_workers
    trigger.name(name)

    return trigger
