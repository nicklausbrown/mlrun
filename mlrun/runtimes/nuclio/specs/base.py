from enum import Enum
from typing import Dict, List, Union, Optional
from pydantic import Field

from . import VolumeSpec, CamelBaseModel
from .code_entry import CodeEntryType, CodeEntryAttributes
from .trigger import Trigger


class FunctionMetadata(CamelBaseModel):
    """ Nuclio function metadata

    Learn more here: https://nuclio.io/docs/latest/reference/function-configuration/function-configuration-reference/#function-metadata-metadata

    Attributes
    ----------
    name : str
        The name of the function
    namespace : str
        A level of isolation provided by the platform (e.g., Kubernetes)
    labels : dict
        A dict that is used for looking up the function (immutable, can't update after first deployment)
    annotations : dict
        A dict of annotations

    """
    name: str = 'nuclio-function'
    namespace: str = 'nuclio'
    labels: Dict[str, str] = Field(default_factory=lambda: dict())
    annotations: Dict[str, str] = Field(default_factory=lambda: dict())


class BuildSpec(CamelBaseModel):
    """ Nuclio function build specification

    Many of these values have default values that can be found here:
    https://nuclio.io/docs/latest/reference/function-configuration/function-configuration-reference/#function-specification-spec

    For code entry types, learn more here:
    https://nuclio.io/docs/latest/reference/function-configuration/code-entry-types/

    Attributes
    ----------
    path : str, optional
        The URL of a GitHub repository or an archive-file that contains the function code — for the github or archive
        code-entry type — or the URL of a function source-code file
    function_source_code : str, optional
        Base-64 encoded function source code for the sourceCode code-entry type
    code_entry : CodeEntryType, optional
        The function's code-entry type - sourceCode | archive | github | image | s3
    code_entry_attributes : Union[S3Attributes, ArchiveAttributes, GithubAttributes], optional
        Code-entry attributes, which provide information for downloading the function when using github, s3, or archive
    registry : str, optional
        The container image repository to which the built image will be pushed
    base_image : str, optional
        The name of a base container image from which to build the function's processor image
    onbuild_image : str, optional
        The name of an "onbuild" container image from which to build the function's processor image
    no_cache : bool, optional
        Do not use any caching when building container images
    no_base_image_pull : bool, optional
        Do not pull any base images when building, use local images only
    commands : List[str], optional
        Commands run opaquely as part of container image build
    image : str
        The name of the built container image (default: the function name)

    """

    path: Optional[str] = None
    function_source_code: Optional[str] = None

    code_entry_type: Optional[CodeEntryType] = None
    code_entry_attributes: Optional[CodeEntryAttributes] = None

    registry: Optional[str] = None
    base_image: Optional[str] = None
    onbuild_image: Optional[str] = None

    no_cache: Optional[bool] = None
    no_base_image_pull: Optional[bool] = None

    commands: Optional[List[str]] = Field(default_factory=lambda: list(), alias='Commands')

    image: Optional[str] = None


class EnvVariableSpec(CamelBaseModel):
    """ Mapping of name to value for the environment

    Attributes
    ----------
    name : str
        Variable name
    value : str
        Variable value

    """
    name: str
    value: str


class SecurityContextSpec(CamelBaseModel):
    """ Container security spec

    Attributes
    ----------
    run_as_user : int
        The user ID (UID) for runing the entry point of the container process
    run_as_group : int
        The group ID (GID) for running the entry point of the container process
    fs_group: int
        A supplemental group to add and use for running the entry point of the container process

    """
    run_as_user: int = None
    run_as_group: int = None
    fs_group: int = None


class ResourcesSpec(CamelBaseModel):
    """ K8s style resource specification

    Check it out here: https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/
    #requests-and-limits

    Attributes
    ----------
    requests : Resources
        Resource requests
    limits : Resources
        Resource limits

    """

    class Resources(CamelBaseModel):
        """ K8s style resource specification

        Check it out here: https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/
        #requests-and-limits

        Attributes
        ----------
        cpu : int, optional
            number of cpus available to the replica
        memory : str, optional
            amount of memory available to the replica
        gpu : str, optional
            number of gpus available to the replica

        """
        cpu: Optional[int] = None
        memory: Optional[str] = None
        gpu: Optional[str] = Field(default=None, alias='nvidia.com/gpu')

    requests: Resources = Resources()
    limits: Resources = Resources()


class PlatformRestartPolicy(CamelBaseModel):
    name: str = None
    maximum_retry_count: int = None


class PlatformMountOptions(Enum):
    bind = "bind"
    volume = "volume"


class PlatformSpec(CamelBaseModel):
    """ Nuclio platform specifications for the deployment engine specifications - Docker, K8s, etc.

    """

    class Attributes(CamelBaseModel):
        """ Only nuclio platform specs

        restart_policy: PlatformRestartPolicy
            The name of the restart policy for the function-image container
        mount_mode: PlatformMountOptions
            Function mount mode, which determines how Docker mounts the function configurations - bind | volume
            (default: bind)

        """

        restart_policy: PlatformRestartPolicy = PlatformRestartPolicy()
        mount_mode: Union[PlatformMountOptions, str] = PlatformMountOptions.bind

    attributes: Attributes = Attributes()


class NuclioPythonSpec(CamelBaseModel):
    """ Nuclio function highest level specification

    Learn more here: https://nuclio.io/docs/latest/reference/function-configuration/function-configuration-reference/#function-specification-spec

    Attributes
    ----------
    runtime : str
        The name of the language runtime (python:3.6, python:3.7, etc.)
    handler : str
        The entry point to the function, in the form of package:entrypoint; varies slightly between runtimes, see the
         appropriate runtime documentation for specifics
    description : str, optional
        A textual description of the function
    image : str, optional
        Potential code entry type for specifying a nuclio function as a docker image directly
    min_replicas : int, optional
        The minimum number of replicas
    max_replicas : int, optional
        The maximum number of replicas
    replicas : int, optional
        The number of desired instances; 0 for auto-scaling.
    target_cpu : int, optional
        Target CPU when auto scaling, as a percentage (default: 75%)
    readiness_timeout_seconds : int, optional
        Number of seconds that the controller will wait for the function to become ready before declaring
        failure (default: 60)
    event_timeout : int, optional
        Global event timeout, in the format supported for the Duration parameter of the time.ParseDuration Go function
    avatar : str, optional
        Base64 representation of an icon to be shown in UI for the function
    run_registry : str, optional
        The container image repository from which the platform will pull the image
    env : list
        A list of environment variables dicts or specs
    volumes : list
        A list in an architecture similar to Kubernetes volumes
    triggers : dict
        A dict of triggers for a nuclio function like http or kafka
    resources : ResourcesSpec, optional
        Limit resources allocated to deployed function
    platform : PlatformSpec, optional
        Docker options for nuclio functions
    security_context : SecurityContextSpec, optional
        Unix style image security constraints like users and groups

    """
    runtime: str = "python:3.7"
    handler: str = "main:handler"
    description: Optional[str] = None

    image: Optional[str] = None

    min_replicas: Optional[int] = 1
    max_replicas: Optional[int] = 2
    replicas: Optional[int] = None  # should this be zero?
    target_cpu: Optional[int] = Field(default=None, alias="targetCPU")

    readiness_timeout_seconds: Optional[int] = None
    event_timeout: Optional[int] = None
    avatar: Optional[str] = None
    run_registry: Optional[str] = None

    env: List[EnvVariableSpec] = Field(default_factory=lambda: list())
    volumes: List[VolumeSpec] = Field(default_factory=lambda: list())
    triggers: Dict[str, Trigger] = Field(default_factory=lambda: dict())
    resources: Optional[ResourcesSpec] = ResourcesSpec()
    platform: Optional[PlatformSpec] = PlatformSpec()
    security_context: Optional[SecurityContextSpec] = SecurityContextSpec()
    build: Optional[BuildSpec] = BuildSpec()


class NuclioConfig(CamelBaseModel):

    api_version: str = "nuclio.io/v1"
    kind: str = "NuclioFunction"
    metadata: FunctionMetadata = FunctionMetadata()
    spec: NuclioPythonSpec = NuclioPythonSpec()

    def add_env(self, variable: Union[Dict, EnvVariableSpec]):
        if type(variable) is dict:
            for key, value in variable.items():
                self.spec.env.append(EnvVariableSpec(name=key, value=value))
        else:
            self.spec.env.append(variable)

    def add_volume(self, volume: VolumeSpec):
        self.spec.volumes.append(volume)

    def add_trigger(self, trigger: Trigger):
        self.spec.triggers[trigger.name()] = trigger
