from typing import Any, Type

from fastapi import Depends

from ayon_server.addons import BaseServerAddon
from ayon_server.api.dependencies import dep_current_user, dep_project_name
from ayon_server.entities import FolderEntity, UserEntity
from ayon_server.exceptions import NotFoundException
from ayon_server.lib.postgres import Postgres

from .settings import ImportSettings


class OpenPypeImportAddon(BaseServerAddon):
    name = "op3import"
    title = "OpenPype import"
    version = "1.0.0"
    settings_model: Type[ImportSettings] = ImportSettings

    frontend_scopes: dict[str, Any] = {"settings": {}}
    # services = {"SplinesReticulator": {"image": "bfirsh/reticulate-splines"}}

    def initialize(self):
        return
        self.add_endpoint(
            "get-random-folder/{project_name}",
            self.get_random_folder,
            method="GET",
        )

    async def setup(self):
        """Setup method is called after the addon is registered"""
        return

    async def get_random_folder(
        self,
        user: UserEntity = Depends(dep_current_user),
        project_name: str = Depends(dep_project_name),
    ):

        return {}
