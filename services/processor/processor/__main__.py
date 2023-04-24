import os
import time
import shutil
import zipfile

from .common import config
from .ayon import ayon
from .parser import create_sqlite_db
from .deploy import deploy_project


def process(source_event_id: str, target_event_id: str) -> None:
    zip_path = "/tmp/source.zip"
    source_dir = "/tmp/project"

    # delete original files if they exist
    if os.path.exists(zip_path):
        os.remove(zip_path)

    if os.path.exists(source_dir):
        shutil.rmtree(source_dir)

    ayon.update_event(
        target_event_id,
        status="in_progress",
        decsription="Downloading source file",
    )

    try:
        ayon.download_private_file(source_event_id, zip_path)
        assert os.path.getsize(zip_path) > 0, "Source file is empty"
    except Exception as e:
        print(e)
        ayon.update_event(target_event_id, status="error", description=str(e))
        return

    if not os.path.exists(source_dir):
        os.mkdir(source_dir)

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(source_dir)

    source_path = os.path.join(source_dir, "project.json")
    sqlite_path = os.path.join(source_dir, "project.db")
    thumbnail_dir = os.path.join(source_dir, "thumbnails")
    if not os.path.isdir(thumbnail_dir):
        thumbnail_dir = None

    assert os.path.isfile(source_path), "Source file does not exist"

    ayon.update_event(
        target_event_id,
        status="in_progress",
        description="Creating intermediate database",
    )

    actual_project_name = create_sqlite_db(source_path, sqlite_path)

    assert os.path.isfile(sqlite_path), "SQLite database could not be created"

    # Update events with actual project name

    ayon.update_event(
        target_event_id,
        status="in_progress",
        project=actual_project_name,
        description="Deploying project",
    )

    ayon.update_event(
        source_event_id,
        project=actual_project_name,
    )

    deploy_project(sqlite_path, thumbnail_dir)


def main():
    while True:
        req = {
            "sourceTopic": "openpype_import.upload",
            "targetTopic": "openpype_import.process",
            "sender": config.service_name,
            "description": "Importing project",
        }
        try:
            res = ayon.post("enroll", json=req)
        except Exception as e:
            print(e)
            time.sleep(5)
            continue

        if res is None:
            time.sleep(5)
            continue

        source_event_id = res["dependsOn"]
        target_event_id = res["id"]
        source_event = ayon.get(f"events/{source_event_id}")
        project_name = source_event["project"]
        user_name = source_event["user"]

        ayon.update_event(
            source_event_id,
            project=project_name,
            user=user_name,
            status="finished",
        )

        ayon.update_event(
            target_event_id,
            project=project_name,
            user=user_name,
            description="Waiting for source file",
            status="in_progress",
        )

        try:
            process(source_event_id, target_event_id)
        except Exception as e:
            print("Error while processing")
            print(e)
            ayon.update_event(target_event_id, status="failed", description=str(e))
            continue

        ayon.update_event(
            target_event_id,
            status="finished",
            description="Successfully imported",
        )


if __name__ == "__main__":
    main()
