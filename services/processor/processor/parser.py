import json
import logging
import time
import sqlite3

from typing import Any, Generator
from .common import mongoid2uuid


VALID_TYPES = [
    "project",
    "asset",
    "subset",
    "version",
    "hero_version",
    "representation",
    "workfile",
]


SQLITE_SCHEMA = """
    CREATE TABLE IF NOT EXISTS entities (
        id TEXT PRIMARY KEY,
        type TEXT,
        entity_type TEXT,
        parent TEXT,
        visual_parent TEXT,
        source_version TEXT,
        name TEXT,
        data TEXT
    );
"""

SCHEMA_INDICES = [
    "CREATE INDEX IF NOT EXISTS entities_type_idx ON entities (type);",
    "CREATE INDEX IF NOT EXISTS entities_entity_type_idx ON entities (entity_type);",
    "CREATE INDEX IF NOT EXISTS entities_parent_idx ON entities (parent);",
    "CREATE INDEX IF NOT EXISTS entities_visual_parent_idx ON entities (visual_parent);",
    "CREATE INDEX IF NOT EXISTS entities_source_version_idx ON entities (source_version);",
]

# Fields we don't want to move from the top level to data
HANDLED_TLC = ["_id", "data", "name", "parent", "type", "schema"]


def is_list_of_jsons(source_path: str) -> bool:
    """Check if the source file is a list of JSONs"""
    with open(source_path, "r") as source_file:
        first_line = source_file.readline()
        return not first_line.startswith("[")


def source_iterator(source_path: str) -> Generator[dict[str, Any], None, None]:
    """Iterate over the source file and yield each entity"""

    if is_list_of_jsons(source_path):
        logging.info("Source file is a list of JSONs")
        with open(source_path, "r") as source_file:
            for line in source_file:
                yield json.loads(line)
    else:
        with open(source_path, "r") as source_file:
            data = json.load(source_file)
            for entity in data:
                yield entity


def parse_mongo_id(mongo_id: str) -> str:
    """Create a UUID from the MongoDB ID"""
    original_id = mongo_id["$oid"]
    return mongoid2uuid(original_id)


def parse_mongo_date(mongo_date: str) -> str:
    """Convert a MongoDB date to a string"""
    return None
    return time.strftime("%Y-%m-%d", time.gmtime(mongo_date["$date"] / 1000))


def replace_mongo_types(obj: dict[str, Any] | list[Any]) -> dict[str, Any] | list[Any]:
    """Recursively replace $numberInt, $numberDouble, $numberLong,
    and $oid types with native types"""

    if isinstance(obj, dict):
        for key, value in obj.items():
            if (
                isinstance(value, dict)
                and len(value) == 1
                and list(value.keys())[0].startswith("$")
            ):
                value_key = list(value.keys())[0]
                if value_key == "$numberInt":
                    obj[key] = int(obj[key][value_key])
                elif value_key == "$numberDouble":
                    obj[key] = float(obj[key][value_key])
                elif value_key == "$numberLong":
                    obj[key] = int(obj[key][value_key])
                elif value_key == "$oid":
                    obj[key] = parse_mongo_id(obj[key])
                elif value_key == "$date":
                    obj[key] = parse_mongo_date(obj[key])
                else:
                    logging.warning(f"Unhandled MongoDB type: {obj[key]}")
            elif isinstance(obj[key], dict):
                replace_mongo_types(obj[key])

            elif isinstance(obj[key], list):
                obj[key] = [replace_mongo_types(item) for item in obj[key]]

            else:
                pass  # Do nothing, since the value is not a MongoDB type
    return obj


def create_sqlite_db(source_path: str, sqlite_path: str) -> str:
    """Parse the MongoDB JSON file and create a SQLite database

    We need this to do fast lookups of the data.
    Fields needed for search are converted to columns,
    the rest is cleaned up and stored as JSON in 'data' column.

    Clean-up involves converting mongo IDs to UUIDs, converting
    mongo types to naive json values, and removing fields that
    are not needed at all.

    The intermediate database is stored as a file, so it can be
    used for multiple imports.

    Returns a parsed project name
    """

    # start_time = time.time()
    # with open(source_path, "r") as f:
    #     source_data = json.load(f)
    # logging.debug(f"Source file loaded {time.time() - start_time:.2f}s")
    # logging.info("Opening SQLite database")

    actual_project_name = None
    with sqlite3.connect(sqlite_path) as conn:
        db = conn.cursor()
        db.execute("DROP TABLE IF EXISTS entities;")
        db.execute(SQLITE_SCHEMA)
        for index in SCHEMA_INDICES:
            db.execute(index)

        i = 0
        start_time = time.time()
        logging.info("Opening source file")
        for row in source_iterator(source_path):

            # Clean-up mongo types
            row = replace_mongo_types(row)

            if (_type := row.get("type")) not in VALID_TYPES:
                continue

            _data = row.get("data", {})

            # Payload stores attributes, config and stuff

            payload = _data
            for key, value in row.items():
                if key in HANDLED_TLC:
                    continue
                payload[key] = value

            if _type == "project":
                actual_project_name = row.get("name")

            # Versions don't have a name, so we use the version number

            if _type == "version":
                name = None
                payload["version"] = int(row["name"])
            else:
                name = row.get("name")

            # for hero versions...
            if _type == "hero_version":
                source_version = payload.pop("version_id")
            else:
                source_version = None

            # Visual parent

            visual_parent = payload.pop("visualParent", None)

            # Entity type (A.K.A. folder type in Ayon)
            # We need is as a column to be able to do distinct
            # and build foldertypes in the import

            entity_type = payload.pop("entityType", None)

            # keys renaming:
            # - tools_env -> tools

            if "tools_env" in payload:
                payload["tools"] = payload.pop("tools_env")

            # Construct DB row

            parsed_row = {
                "id": row["_id"],
                "type": _type,
                "entity_type": entity_type,
                "parent": row["parent"] if row.get("parent") else None,
                "visual_parent": visual_parent,
                "source_version": source_version,
                "name": name,
                "data": json.dumps(payload),
            }

            db.execute(
                """
                INSERT INTO entities VALUES (
                    :id,
                    :type,
                    :entity_type,
                    :parent,
                    :visual_parent,
                    :source_version,
                    :name,
                    :data
                )
                """,
                parsed_row,
            )
            i += 1
            if i % 1000 == 0:
                logging.info(f"Inserted {i} rows into SQLite database")

        logging.info("Removing orphaned subsets")
        db.execute(
            """
            DELETE FROM entities
            WHERE type = 'subset'
            AND parent NOT IN (SELECT id FROM entities WHERE type = 'asset')
            """
        )

        logging.info("Removing orphaned versions")
        db.execute(
            """
            DELETE FROM entities
            WHERE type = 'version'
            AND parent NOT IN (SELECT id FROM entities WHERE type = 'subset')
            """
        )

        logging.info("Removing orphaned representations")
        db.execute(
            """
            DELETE FROM entities
            WHERE type = 'representation'
            AND parent NOT IN (SELECT id FROM entities WHERE type IN ('version', 'hero_version'))
            """
        )

        logging.info("Removing versions without representations")
        db.execute(
            """
            DELETE FROM entities
            WHERE type = 'version'
            AND id NOT IN (SELECT parent FROM entities WHERE type = 'representation')
            """
        )

        logging.info("Removing subsets whithout versions")
        db.execute(
            """
            DELETE FROM entities
            WHERE type = 'subset'
            AND id NOT IN (SELECT parent FROM entities WHERE type = 'version')
            """
        )


        logging.info(f"Inserted {i} rows into SQLite database")
        logging.info(f"SQLite database created {time.time() - start_time:.2f}s")

    return actual_project_name
