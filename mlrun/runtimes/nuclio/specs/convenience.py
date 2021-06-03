import os
from typing import List, Union, Dict
from . import KafkaTrigger, HttpTrigger, V3ioStreamTrigger, CronTrigger, VolumeSpec, Volume
from .trigger import HttpIngresses


def create_v3io_trigger(
    path: str,
    container: str = 'users',
    access_key: str = None,
    max_workers: int = 1,
    name: str = 'v3io-stream'
) -> V3ioStreamTrigger:
    """Convenience function for creating a v3io stream trigger object

    Additional specialized parameters can be declared on the trigger object
    which is returned. See function body for examples of how to do this.

    https://nuclio.io/docs/latest/reference/triggers/v3iostream/

    Parameters
    ----------
    path : str
        Path in container for stream location
    container : str, optional
        V3io container name to map path into, defaults to user
    access_key : str, optional
        V3io access key, defaults to V3IO_ACCESS_KEY in the environment
    max_workers : int, optional
        Maximum amount of workers dedicated to this trigger in a replica, defaults to 1
    name : str, optional
        Name for the trigger, defaults to v3io-stream

    Returns
    -------
    V3ioStreamTrigger object

    """

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
    """Convenience function for creating a kafka trigger object

    Additional specialized parameters can be declared on the trigger object
    which is returned. See function body for examples of how to do this.

    https://nuclio.io/docs/latest/reference/triggers/kafka/

    Parameters
    ----------
    topic : str, List[str]
        Topic name or in special circumstances a list of topic names
    brokers : List[str]
        List of broker IPs or Domains
    partitions: List[int], optional
        List of integers of the partitions to trigger on, defaults to [0] (single partition)
    consumer_group: str, optional
        Name of the consumer group to apply to this function trigger, defaults to nuclio-function
    max_workers : int, optional
        Maximum amount of workers dedicated to this trigger in a replica, defaults to 1
    name : str, optional
        Name for the trigger, defaults to kafka-topic

    Returns
    -------
    KafkaTrigger object

    """

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
    port: int = 32001,
    ingresses: Dict[str, HttpIngresses] = None,
    max_workers: int = 1,
    name: str = 'http'
) -> HttpTrigger:
    """Convenience function for creating an http trigger object

    Additional specialized parameters can be declared on the trigger object
    which is returned. See function body for examples of how to do this.

    https://nuclio.io/docs/latest/reference/triggers/http/

    Parameters
    ----------
    port : int, optional
        Port on which the trigger will listen, defaults to 32001
    ingresses : Dict[str, HttpIngresses], optional
        Dictionary of http ingresses with the name mapped to an HttpIngresses object
    max_workers : int, optional
        Maximum amount of workers dedicated to this trigger in a replica, defaults to 1
    name : str, optional
        Name for the trigger, defaults to http

    Returns
    -------
    HttpTrigger object

    """

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
    """Convenience function for creating an HttpIngresses object

    - Kubernetes documentation: https://kubernetes.io/docs/concepts/services-networking/ingress/
    - Nuclio documentation: https://nuclio.io/docs/latest/reference/triggers/http/

    Parameters
    ----------
    name : str
        Name for ingress object, returned as Dict key
    host : str
        Host to which the ingress maps
    paths : List[str]
        The paths that the ingress handles. Variables of the form {{.<NAME>}} can be specified using .Name, .Namespace,
        and .Version. For example, /{{.Namespace}}-{{.Name}}/{{.Version}} will result in a default ingress of
         /namespace-name/version.

    Returns
    -------
    Dictionary mapping the name to an HttpIngresses object

    """

    ingress = HttpIngresses()
    ingress.host = host
    ingress.paths = paths
    return {name: ingress}


def create_cron_trigger(
    schedule: str = None,
    interval: str = None,
    event_body: str = None,
    event_headers: Dict[str, Union[int, str]] = None,
    max_workers: int = 1,
    name: str = 'cron'
) -> CronTrigger:
    """Convenience function for creating a cron trigger object

    Additional specialized parameters can be declared on the trigger object
    which is returned. See function body for examples of how to do this.

    https://nuclio.io/docs/latest/reference/triggers/cron/

    Parameters
    ----------
    schedule : str, optional
        Cron-like schedule (for example, */5 * * * *), cannot be declared with interval parameter
    interval : str, optional
        Interval (for example, 1s, 30m), cannot be declared with schedule parameter
    event_body : str, optional
        Body passed in the event object
    event_headers : Dict[str, Union[int, str]], optional
        Headers passed in the event object
    max_workers : int, optional
        Maximum amount of workers dedicated to this trigger in a replica, defaults to 1
    name : str, optional
        Name for the trigger, defaults to http

    Returns
    -------
    CronTrigger object

    """

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


def create_volume(
    volume: Volume,
    function_path: str,
    volume_target: str
) -> VolumeSpec:
    """Convenience function for creating a volume spec with associated volume mapping

    See subclasses of Volume object for options.

    Parameters
    ----------
    volume : Volume
        Volume object to use in the volume spec (for example V3ioVolume())
    function_path : str
        Path to map volume into inside the function
    volume_target : str
        Associated volume object target string, see volume objects (for example HostVolume)

    Returns
    -------
    VolumeSpec object

    """

    volume_spec = VolumeSpec(volume=volume)
    volume_spec.map(function_path=function_path, volume_target=volume_target)
    return volume_spec
