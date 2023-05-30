import json
import sqlite3

from typing import Generator, Any
from .common import config


def parse_version(
    version_id: str,
    parent_id: str,
    version_data: dict[str, Any],
    version_number: int,
    thumbnails: dict[str, str] | None = None,
) -> dict[str, Any]:

    # just let the api handle the validation
    # and exclude invalid keys
    original_author = version_data.pop("author", None)
    attributes = {**version_data}

    if thumbnails and version_data.get("thumbnail_id"):
        thumbnail_id = thumbnails.get(version_data["thumbnail_id"])
    else:
        thumbnail_id = None

    return {
        "type": "create",
        "entityType": "version",
        "entityId": version_id,
        "data": {
            "productId": parent_id,
            "thumbnailId": thumbnail_id,
            "version": version_number,
            "attrib": attributes,
            "author": config.default_author,
            "status": config.default_status,
            "data": {
                "originalAuthor": original_author,
            },
        },
    }


def get_hero_versions(
    conn: sqlite3.Connection,
    thumbnails,
) -> Generator[dict[str, Any], None, None]:
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT h.id AS hero_id, v.parent, v.data
        FROM entities AS h
        INNER JOIN entities AS v ON h.source_version = v.id
        """
    )
    for row in cursor.fetchall():
        version_id = row[0]
        parent_id = row[1]
        version_data = json.loads(row[2])
        version_number = -version_data["version"]

        yield parse_version(version_id, parent_id, version_data, version_number, thumbnails)


def get_versions(conn: sqlite3.Connection, thumbnails) -> Generator[dict[str, Any], None, None]:
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, parent, data
        FROM entities WHERE type = 'version'
        -- AND parent IN (SELECT id FROM entities WHERE type = 'subset')
        -- AND id IN (SELECT parent FROM entities WHERE type = 'representation')
        """
    )

    for row in cursor.fetchall():
        version_id = row[0]
        parent_id = row[1]
        version_data = json.loads(row[2])
        version_number = version_data["version"]


        yield parse_version(version_id, parent_id, version_data, version_number, thumbnails)
