import os
import json
import sqlite3
import time
import logging

from typing import Any, Generator

from .checks import run_checks
from .project import parse_project
from .common import mongoid2uuid
from .ayon import ayon
from .folders import folders_by_parent
from .subsets import get_subsets
from .versions import get_versions, get_hero_versions
from .representations import get_representations

BATCH_SIZE = 100


def deploy(conn: sqlite3.Connection, thumbnail_dir: str | None = None):
    start_time = time.monotonic()
    db = conn.cursor()
    db.execute("SELECT name, data FROM entities WHERE type = 'project'")

    project_row = db.fetchone()

    assert project_row, "No project found in database"

    db.execute(
        """
        SELECT DISTINCT (entity_type) FROM entities
        WHERE entity_type IS NOT NULL AND entity_type != 'Project'
        """
    )
    folder_types = [row[0] for row in db.fetchall()]

    assert folder_types, "No folder types found in database"

    # Force load task types

    db.execute(" SELECT data FROM entities WHERE type = 'asset'")
    used_task_types = set()
    for row in db.fetchall():
        data = json.loads(row[0])
        for task_name, task in data.get("tasks", {}).items():
            used_task_types.add(task["type"].lower())

    # Deploy project
    logging.info("Deploying project")

    project = parse_project(*project_row, folder_types, used_task_types)
    project_name = project["name"]

    try:
        ayon.delete(f"projects/{project_name}")
    except Exception:
        pass
    else:
        logging.info("Deleted existing project")
    ayon.post("projects", json=project)

    # TOOOL

    def execute_ops(ops: list[dict[str, Any]]) -> int:
        counter = 0
        if not ops:
            return 0
        res = ayon.post(
            f"projects/{project_name}/operations",
            json={"operations": ops, "canFail": True},
        )
        if not (res["success"]):
            for res_op in res["operations"]:
                if not res_op["success"]:
                    msg = (
                        f"Unable to deploy {res_op['entityType']} {res_op['entityId']}"
                    )
                    if detail := res_op.get("detail"):
                        msg += f": {detail}"
                    logging.error(msg)
                else:
                    counter += 1
        else:
            counter += len(ops)
        return counter

    def bach_process_ops(ops_generator: Generator[dict[str, Any], None, None]):
        ops = []
        counter = 0
        for op in ops_generator:
            ops.append(op)
            if len(ops) >= BATCH_SIZE:
                counter += execute_ops(ops)
                ops = []
        counter += execute_ops(ops)
        return counter

    # Deploy thumbnails (stupid, but we need them first)

    thumbnails = {}
    print(thumbnail_dir)
    if thumbnail_dir:
        for path in os.listdir(thumbnail_dir):
            if path.endswith(".jpg"):
                original_id = mongoid2uuid(path.split("_")[0])
                logging.info(f"Deploying thumbnail {original_id}")
                with open(os.path.join(thumbnail_dir, path), "rb") as f:
                    response = ayon.post(
                        f"projects/{project_name}/thumbnails",
                        headers={"Content-Type": "image/jpeg"},
                        data=f.read(),
                    )
                    if response:
                        thumbnails[original_id] = response["id"]

    # Deploy folders and tasks
    # We need to do this per-parent to ensure the parent exists
    # before the child is created.

    logging.info("Deploying folders and tasks")

    def deploy_folders(parent_id: str | None) -> int:
        ops = []
        children_ids = []
        counter = 0
        for operation in folders_by_parent(parent_id, conn, thumbnails=thumbnails):
            ops.append(operation)
            if "entityId" in operation:
                children_ids.append(operation["entityId"])

        counter += execute_ops(ops)

        for child_id in children_ids:
            counter += deploy_folders(child_id)
        return counter

    count = deploy_folders(None)
    logging.info(f"Deployed {count} folders and tasks")

    logging.info("Deploying subsets")
    count = bach_process_ops(get_subsets(conn))
    logging.info(f"Deployed {count} subsets")

    logging.info("Deploying versions")
    count = bach_process_ops(get_versions(conn, thumbnails))
    logging.info(f"Deployed {count} versions")

    logging.info("Deploying hero versions")
    count = bach_process_ops(get_hero_versions(conn, thumbnails))
    logging.info(f"Deployed {count} hero versions")

    logging.info("Deploying representations")
    count = bach_process_ops(get_representations(conn))
    logging.info(f"Deployed {count} representations")

    logging.info(f"Deployed in {time.monotonic() - start_time:.2f}s")


#
# Main
#


def deploy_project(sqlite_path: str, thumbnail_dir: str | None = None):
    assert os.path.exists(sqlite_path), "SQLite database does not exist"
    is_error = False
    with sqlite3.connect(sqlite_path) as conn:
        run_checks(conn)
        try:
            deploy(conn, thumbnail_dir)
        except AssertionError as e:
            logging.critical(e)
            is_error = True

    if is_error:
        print()
        raise SystemExit(1)
