import socket
import logging
import uuid

from rich.logging import RichHandler
from rich.console import Console
from pydantic import BaseSettings, Field

# Set up logging

handler = RichHandler(level="DEBUG", console=Console())
handler.setFormatter(logging.Formatter("%(message)s"))
logging.basicConfig(level="INFO", handlers=[handler])


def mongoid2uuid(mongoid: str) -> str:
    """Convert a MongoDB ID to a UUID"""
    return uuid.uuid5(uuid.NAMESPACE_OID, mongoid).hex


class Config(BaseSettings):
    """Configuration for the import"""

    api_key: str = Field(
        ...,
        title="API key",
        description="API key to access the Ayon API",
        env="ayon_api_key",
    )
    server_url: str = Field(
        "http://localhost:5000",
        title="Ayon server host",
        description="URL of the running ayon instance",
        env="ayon_server_url",
    )
    addon_name: str = Field(
        ...,
        title="Addon name",
        env="ayon_addon_name",
    )
    addon_version: str = Field(
        ...,
        title="Addon version",
        env="ayon_addon_version",
    )
    service_name: str = Field(
        default_factory=socket.gethostname,
        env="ayon_service_name",
    )

    force: bool = Field(
        False,
        title="Force",
        description="Force intermediate database creation",
    )
    default_status = Field(
        "Not ready",
        title="Default status",
        description="Status to be applied to migrated entities",
    )
    default_author = Field(
        "migration",
        title="Default author",
        description="Author to be applied to migrated entities",
    )

    class Config:
        case_sensitive = False
        env_file = ".env"
        env_file_encoding = "utf-8"


config = Config()
