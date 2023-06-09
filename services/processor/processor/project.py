import json
import logging

from typing import Any


def parse_project(
    project_name: str,
    project_payload: str,
    folder_types: list[str],
    task_type_map: dict[str, Any],
) -> dict[str, Any]:
    project_data = json.loads(project_payload)

    # Unused keys
    project_data.pop("entityType", None)
    project_data.pop("parent", None)
    project_data.pop("schema", None)

    library = project_data.pop("library_project", None) or False
    project_code = project_data.pop("code", project_name[:3].lower())
    project_config = project_data.pop("config", {})

    # TODO
    _ = project_data.pop("active", True)

    #
    # Build anatomy
    #

    anatomy = {
        "folder_types": [],
        "task_types": [],
        "roots": [],
        "templates": {},
        "attributes": {},
        # OP 3 does not support statuses and tags, but Ayon provide defaults
        # "statuses": [],
        # "tags": [],
    }

    # folder_types

    for folder_type in folder_types:
        anatomy["folder_types"].append({"name": folder_type})

    # task types

    task_types = project_config.pop("tasks", {})
    for key, value in task_types.items():
        short_name = value.get("short_name", key)
        task_type_map[key.lower()] = {"name": key, "shortName": short_name}

    for task_type_key, value in task_type_map.items():
        anatomy["task_types"].append(value)

    # roots

    project_roots = project_config.pop("roots", {})
    for key, value in project_roots.items():
        anatomy["roots"].append({"name": key, **value})

    # templates

    project_templates = project_config.pop("templates", {})
    defaults = project_templates.pop("defaults", {})
    template_res = {
        "version_padding": int(defaults["version_padding"]),
        "frame_padding": int(defaults["version_padding"]),
        "frame": defaults["frame"],
    }

    # TODO: others have to be handled differently
    project_templates.pop("others", {})

    for key, value in project_templates.items():
        if not value:
            continue
        try:
            template_res[key] = [
                {
                    "name": "default",
                    "directory": value["folder"],
                    "file": value["file"],
                    "path": value["path"],
                }
            ]
        except Exception:
            logging.warning(f"Could not parse template {key}")

    anatomy["templates"] = template_res

    # Attributes

    # assume the rest of the project config is attributes
    for key, value in project_data.items():
        anatomy["attributes"][key] = value

    # apps
    rapps: list[str] = []
    applications = project_config.pop("apps", [])
    for application in applications:
        rapps.append(application["name"])
    anatomy["attributes"]["apps"] = rapps

    # TODO
    # project_apps = project_config.pop("apps", [])
    # project_imageio = project_config.pop("imageio", {})

    # build the result

    return {
        "name": project_name,
        "code": project_code,
        "library": library,
        "anatomy": anatomy,
    }
