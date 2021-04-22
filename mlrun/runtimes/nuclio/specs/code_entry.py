from enum import Enum
from typing import Optional
from pydantic import SecretStr, Field

from . import CamelBaseModel


class CodeEntryType(Enum):
    s3 = 's3'
    github = 'github'
    archive = 'archive'


class S3Attributes(CamelBaseModel):
    s3_bucket: str
    s3_item_key: str
    s3_access_key_id: Optional[str] = None
    s3_secret_access_key: Optional[SecretStr] = None
    s3_session_token: Optional[str] = None
    s3_region: Optional[str] = None
    work_dir: Optional[str] = None


class ArchiveAttributes(CamelBaseModel):

    class Headers(CamelBaseModel):
        v3io_key: str = Field(default=None, alias='X-V3io-Session-Key')

    headers: Headers = Headers()
    work_dir: Optional[str] = None


class GithubAttributes(CamelBaseModel):

    class Headers(CamelBaseModel):
        auth_token: str = Field(default=None, alias='Authorization')

    branch: str
    headers: Headers = Headers()
    work_dir: Optional[str] = None
