import os
import aiofiles

from typing import Any, Type

from fastapi import Depends, Request, Response
from nxtools import slugify

from ayon_server.addons import BaseServerAddon
from ayon_server.api.dependencies import dep_current_user
from ayon_server.entities import UserEntity
from ayon_server.events import dispatch_event, update_event
from ayon_server.exceptions import AyonException, BadRequestException
from ayon_server.lib.postgres import Postgres

from .settings import ImportSettings


class OpenPypeImportAddon(BaseServerAddon):
    name = "openpype_import"
    title = "OpenPype import"
    version = "0.2.1"
    settings_model: Type[ImportSettings] = ImportSettings

    frontend_scopes: dict[str, Any] = {"settings": {}}
    services = {"OpenpypeImport": {"image": "ynput/ayon-openpype-import:0.2.1"}}

    def initialize(self):
        self.add_endpoint("import", self.import_project, method="POST")

    async def setup(self):
        """Setup method is called after the addon is registered"""
        return

    async def import_project(
        self,
        request: Request,
        user: UserEntity = Depends(dep_current_user),
    ) -> Response:
        """Import project from OpenPype"""

        project_name = request.headers.get("X-Ayon-Project-Name")
        anatomy_preset = request.headers.get("X-Ayon-Anatomy-Preset")

        # This is not a real project name.
        # it is just a name of the file that is being uploaded,
        # so we can display it in the UI. Import service will
        # update the event later, when the project is actually
        # parsed and imported.

        if not project_name:
            raise BadRequestException("Missing project name")

        anatomy_preset = anatomy_preset or "_"
        if anatomy_preset != "_":
            res = await Postgres.fetch(
                "SELECT name FROM anatomy_presets WHERE name = $1",
                anatomy_preset,
            )
            if not res:
                raise BadRequestException("Invalid anatomy preset")

        project_name = slugify(project_name, separator="_")

        if self.get_private_dir() is None:
            raise AyonException("Private dir does not exist")

        event_id = await dispatch_event(
            "openpype_import.upload",
            user=user.name,
            description="Uploading a project file",
            summary={"anatomy_preset": anatomy_preset},
            project=project_name,
            finished=False,
        )

        target_path = os.path.join(self.get_private_dir(), str(event_id))

        i = 0
        try:
            async with aiofiles.open(target_path, "wb") as f:
                async for chunk in request.stream():
                    i += len(chunk)
                    await f.write(chunk)
        except Exception as e:
            print(e)
            await update_event(
                event_id,
                status="failed",
                description="Failed to upload project file",
            )

            try:
                os.remove(target_path)
            except Exception:
                pass

            raise AyonException("Failed to upload project file")

        await update_event(
            event_id,
            status="finished",
            description="Project file uploaded",
            summary={},
        )

        return Response(status_code=200)
