import os
from abc import ABC, abstractmethod
from typing import Union, Optional
from pydantic import SecretStr, PrivateAttr
from . import CamelBaseModel


class Volume(ABC):

    @abstractmethod
    def target(self, value: str):
        pass


class PersistentVolume(CamelBaseModel, Volume):

    class Attributes(CamelBaseModel):
        claim_name: str = None

    name: str = None
    persistent_volume_claim: Attributes = Attributes()

    def target(self, value: str):
        self.persistent_volume_claim.claim_name = value


class HostVolume(CamelBaseModel, Volume):

    class Attributes(CamelBaseModel):
        path: str = None

    name: str = None
    host_path: Attributes = Attributes()

    def target(self, value: str):
        self.host_path.path = value


class SecretVolume(CamelBaseModel, Volume):

    class Attributes(CamelBaseModel):
        secret_name: str = None

    name: str = None
    secret: Attributes = Attributes()

    def target(self, value: str):
        self.secret.secret_name = value


class V3ioVolume(CamelBaseModel, Volume):

    class Attributes(CamelBaseModel):

        class Options(CamelBaseModel):
            container: str = None
            sub_path: str = None
            access_key: SecretStr = None

        driver: str = 'v3io/fuse'
        options: Options = Options()

    name: str = None
    flex_volume: Attributes = Attributes()

    def target(self, value: str):
        container, sub_path = os.path.normpath(value.lstrip('/')).split(os.sep, maxsplit=1)
        self.flex_volume.options.container = container
        self.flex_volume.options.sub_path = sub_path

    def add_secret(self, secret: str):
        self.flex_volume.options.access_key = SecretStr(secret)


class VolumeSpec(CamelBaseModel):
    """ Volume spec for mapping host file systems into a nuclio function

    Attributes
    ----------
    volume : Union[HostVolume, PersistentVolume, SecretVolume, V3ioVolume]
        Volume subtype to use with volume specification
    volume_mount : VolumeSpec.Mount
        Mount point for function side parameters

    Methods
    -------
    name(name=None)
        Either name a volume or return the name of the volume
    map(function_path, volume_target)
        Convenience method to declare mapping from volume to function

    """

    volume: Union[HostVolume, PersistentVolume, SecretVolume, V3ioVolume]

    class Mount(CamelBaseModel):
        """ Volume spec for mapping host file systems into a nuclio function

        Attributes
        ----------
        name : str
            Mount name
        read_only : bool, optional
            If function can write out to the host
        mount_path : str
            Function path where volume will be mounted

        """
        name: str = None
        read_only: Optional[bool] = None
        mount_path: str = None

    volume_mount = Mount()
    _name: str = PrivateAttr(default='volume')

    def __init__(self, **data):
        super().__init__(**data)
        self._apply_name()

    def name(self, name: str = None):
        """ Apply or return name of volume spec

        Parameters
        ----------
        name : str, optional
            name of the volume

        Returns
        -------
        self

        """
        if name is None:
            return self._name
        else:
            self._name = name
            self._apply_name()
        return self

    def _apply_name(self):
        """ Internal method for keeping volume and volume mount names in sync"""
        self.volume_mount.name = self._name
        self.volume.name = self._name

    def map(self, function_path: str, volume_target: str):
        """ Convenience method to declare mapping from volume to function

        Parameters
        ----------
        function_path : str
            Place to mount volume inside the function
        volume_target : str
            Respective volume name, path, etc. for specification - see specific volumes for target

        """
        self.volume_mount.mount_path = function_path
        self.volume.target(volume_target)

    def add_secret(self, secret: str):
        """ Convenience method to inject a secret into a volume spec

        Parameters
        ----------
        secret : str
            Secret value to associate with a volume

        """
        try:
            self.volume.add_secret(secret)
        except AttributeError as e:
            raise AttributeError(f"Volume doesn't support secrets: {e}")
