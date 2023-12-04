import os
import aiofiles

from typing import Any, Type
from datetime import datetime

from fastapi import Depends, Request, Response
from nxtools import slugify

from ayon_server.addons import BaseServerAddon
from ayon_server.api.dependencies import dep_current_user
from ayon_server.entities import UserEntity
from ayon_server.events import dispatch_event, update_event
from ayon_server.exceptions import AyonException, BadRequestException
from ayon_server.lib.postgres import Postgres
from ayon_server.types import Field, OPModel

from .settings import ImportSettings


class JobSummaryModel(OPModel):
    project: str = Field(..., title="Project name")
    user: str = Field(..., title="User name")
    upload_id: str = Field(..., title="Upload event ID")
    process_id: str | None = Field(None, title="Process event ID")
    description: str = Field(..., title="Upload description")
    status: str = Field(..., title="Upload status")
    updated_at: datetime = Field(..., title="Upload updated at")


class OpenPypeImportAddon(BaseServerAddon):
    name = "openpype_import"
    title = "OpenPype import"
    version = "0.2.3"
    settings_model: Type[ImportSettings] = ImportSettings

    frontend_scopes: dict[str, Any] = {"settings": {}}
    services = {"OpenpypeImport": {"image": "ynput/ayon-openpype-import:0.2.3"}}

    def initialize(self):
        self.add_endpoint("import", self.import_project, method="POST")
        self.add_endpoint("list", self.list_jobs, method="GET")

    async def setup(self):
        """Setup method is called after the addon is registered"""
        return

    async def list_jobs(self) -> list[JobSummaryModel]:
        result = []
        query = """
        SELECT

        u.id as upload_id,
        p.id as process_id,
        u.description as upload_description,
        p.description as process_description,
        u.status as upload_status,
        p.status as process_status,
        u.user_name as user,
        u.project_name as project,
        u.updated_at as upload_updated_at,
        p.updated_at as process_updated_at

        FROM events AS u LEFT JOIN events AS p ON u.id = p.depends_on

        WHERE 
            u.topic = 'openpype_import.upload'

        ORDER BY u.creation_order DESC
        LIMIT 30
        """
        async for row in Postgres.iterate(query):

            description = row["process_description"] or row["upload_description"]
            status = row["process_status"]
            if not status:
                if row["upload_status"] == "failed":
                    status = "failed"
                else:
                    status = "in_progress"

            result.append(
                JobSummaryModel(
                    project=row["project"],
                    user=row["user"],
                    upload_id=row["upload_id"],
                    process_id=row["process_id"],
                    description=description,
                    status=status,
                    updated_at=row["process_updated_at"] or row["upload_updated_at"],
                )
            )

        return result

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
