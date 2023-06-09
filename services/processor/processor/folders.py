import json
import sqlite3
from typing import Any, Generator
from .common import config

NOT_FOLDER_ATTRIB = ["tools_env", "avalon_mongo_id", "parents", "tasks"]


def parse_folder(source: dict[str, Any], thumbnails) -> dict[str, Any]:
    source_data = source["data"]

    payload = {
        "name": source["name"],
        "folderType": source["entity_type"],
        "parentId": source["visual_parent"],
        "attrib": {},
        "status": config.default_status,
    }

    for key, value in source_data.items():
        if key in NOT_FOLDER_ATTRIB:
            continue
        payload["attrib"][key] = value

    # Unused keys
    source.pop("entityType", None)
    source.pop("parent", None)
    source.pop("schema", None)

    if thumbnails and source_data.get("thumbnail_id"):
        if thumbnail := thumbnails.get(source_data["thumbnail_id"]):
            payload["thumbnailId"] = thumbnail

    # TODO
    _ = source.pop("tools_env", None) or []
    _ = source.pop("active", True)

    return {
        "type": "create",
        "entityType": "folder",
        "entityId": source["id"],
        "data": payload,
    }


def folders_by_parent(
    parent_id: str | None,
    conn: sqlite3.Connection,
    thumbnails=None,
    task_type_map=None,
) -> Generator[dict[str, Any], None, None]:
    db = conn.cursor()
    cond = (
        "visual_parent IS NULL"
        if parent_id is None
        else f"visual_parent = '{parent_id}'"
    )
    query = f"""
        SELECT id, name, entity_type, visual_parent, data
        FROM entities WHERE type = 'asset' AND {cond}
        """
    db.execute(query)
    for row in db.fetchall():
        folder_data = json.loads(row[4])
        tasks_data = folder_data.pop("tasks", {})
        yield parse_folder(
            {
                "id": row[0],
                "name": row[1],
                "entity_type": row[2],
                "visual_parent": row[3],
                "data": folder_data,
            },
            thumbnails,
        )

        # In OP3, tasks are stored on Assets (folders),
        # so we deploy the tasks as part of the folder

        for task_name, task_data in tasks_data.items():

            task_type = task_type_map.get(task_data["type"].lower())
            if task_type is None:
                continue
            task_type_name = task_type["name"]

            yield {
                "type": "create",
                "entityType": "task",
                "data": {
                    "folderId": row[0],
                    "name": task_name,
                    "taskType": task_type_name,
                    "status": config.default_status,
                },
            }
