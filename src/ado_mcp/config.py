from typing import Annotated

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

ADO_API_VERSION = "7.1"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ADO_", env_file=".env", extra="ignore"
    )
    org: Annotated[str, Field(min_length=1)]
    project: Annotated[str, Field(min_length=1)]
    pat: SecretStr
