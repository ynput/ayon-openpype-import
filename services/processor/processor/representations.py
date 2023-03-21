import json
import sqlite3

from typing import Generator, Any
from .common import config


def get_representations(
    conn: sqlite3.Connection,
) -> Generator[dict[str, Any], None, None]:
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, parent, name, data
        FROM entities WHERE type = 'representation'
        -- AND parent IN (SELECT id FROM entities WHERE type = 'version')
        """
    )
    for row in cursor.fetchall():
        version_id = row[0]
        parent_id = row[1]
        name = row[2]
        representation_data = json.loads(row[3])

        # files
        files_field = []
        if "files" in representation_data:
            files = representation_data.pop("files", [])
            for file in files:
                file.pop("sites", None)
                file_size = 0
                if "size" in file:
                    file_size = file["size"]
                files_field.append(
                    {
                        "id": file["_id"],
                        "path": file["path"],
                        "size": file_size,
                        "hash": file["hash"],
                        "hash_type": "op3",
                        "name": file.get("name", None),
                    }
                )

        # context goes to data
        data_field = {}
        if "context" in representation_data:
            data_field["context"] = representation_data.pop("context", {})

        # the rest: path, template,.. go to attributes
        attributes = {**representation_data}

        yield {
            "type": "create",
            "entityType": "representation",
            "entityId": version_id,
            "data": {
                "versionId": parent_id,
                "name": name,
                "attrib": attributes,
                "data": data_field,
                "files": files_field,
                "status": config.default_status,
            },
        }
