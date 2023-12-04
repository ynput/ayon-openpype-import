from pydantic import Field

from ayon_server.settings import BaseSettingsModel


class ImportSettings(BaseSettingsModel):
    simple_string: str = Field(
        "default value",
        title="Simple string",
        description="This is a simple string",
    )
