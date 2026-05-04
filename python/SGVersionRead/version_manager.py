from .sg_client import get_sg

_VERSION_FIELDS = [
    "code", "id", "sg_status_list",
    "sg_path_to_frames", "sg_path_to_movie", "sg_uploaded_movie",
    "sg_first_frame", "sg_last_frame",
    "created_at", "updated_at", "sg_task", "entity", "project",
]


def get_projects():
    sg = get_sg()
    return sorted(
        sg.find("Project", [["sg_status", "is", "Active"]], ["name", "id"]),
        key=lambda x: x["name"],
    )


def get_sequences(project_id):
    sg = get_sg()
    return sorted(
        sg.find(
            "Sequence",
            [["project", "is", {"type": "Project", "id": project_id}]],
            ["code", "id"],
        ),
        key=lambda x: x["code"],
    )


def get_shots(project_id, sequence_id=None):
    sg = get_sg()
    filters = [["project", "is", {"type": "Project", "id": project_id}]]
    if sequence_id:
        filters.append(["sg_sequence", "is", {"type": "Sequence", "id": sequence_id}])
    return sorted(sg.find("Shot", filters, ["code", "id"]), key=lambda x: x["code"])


def get_tasks(project_id, shot_id=None, sequence_id=None):
    sg = get_sg()
    filters = [["project", "is", {"type": "Project", "id": project_id}]]
    if shot_id:
        filters.append(["entity", "is", {"type": "Shot", "id": shot_id}])
    elif sequence_id:
        filters.append(["entity", "is", {"type": "Sequence", "id": sequence_id}])
    return sorted(
        sg.find("Task", filters, ["content", "id", "entity"]),
        key=lambda x: x["content"],
    )


def get_versions(task_id=None, shot_id=None, project_id=None, status_list=None):
    sg = get_sg()
    filters = []
    if task_id:
        filters.append(["sg_task", "is", {"type": "Task", "id": task_id}])
    elif shot_id:
        filters.append(["entity", "is", {"type": "Shot", "id": shot_id}])
    elif project_id:
        filters.append(["project", "is", {"type": "Project", "id": project_id}])
    if status_list:
        filters.append(["sg_status_list", "in", status_list])
    return sg.find(
        "Version",
        filters,
        _VERSION_FIELDS,
        order=[{"field_name": "code", "direction": "asc"}],
    )


def get_latest_version(task_id=None, shot_id=None, project_id=None, status_list=None):
    versions = get_versions(task_id, shot_id, project_id, status_list)
    return versions[-1] if versions else None


def get_version_by_id(version_id):
    sg = get_sg()
    return sg.find_one("Version", [["id", "is", version_id]], _VERSION_FIELDS)


def get_version_file_path(version):
    if version.get("sg_path_to_frames"):
        return version["sg_path_to_frames"]
    if version.get("sg_path_to_movie"):
        return version["sg_path_to_movie"]
    movie = version.get("sg_uploaded_movie")
    if movie:
        return movie.get("url", "") if isinstance(movie, dict) else str(movie)
    return ""


def is_latest_version(version_id, task_id=None, shot_id=None, status_list=None):
    latest = get_latest_version(task_id=task_id, shot_id=shot_id, status_list=status_list)
    return latest is None or latest["id"] == version_id


def find_project_by_name(name):
    return get_sg().find_one("Project", [["name", "is", name]], ["name", "id"])


def find_sequence_by_code(code, project_id):
    return get_sg().find_one(
        "Sequence",
        [["code", "is", code], ["project", "is", {"type": "Project", "id": project_id}]],
        ["code", "id"],
    )


def find_shot_by_code(code, project_id):
    return get_sg().find_one(
        "Shot",
        [["code", "is", code], ["project", "is", {"type": "Project", "id": project_id}]],
        ["code", "id"],
    )


def find_task_by_name(name, shot_id=None, project_id=None):
    filters = [["content", "is", name]]
    if shot_id:
        filters.append(["entity", "is", {"type": "Shot", "id": shot_id}])
    if project_id:
        filters.append(["project", "is", {"type": "Project", "id": project_id}])
    return get_sg().find_one("Task", filters, ["content", "id", "entity"])


_status_cache = None


def get_version_statuses():
    """Return {code: name} for valid Version sg_status_list values."""
    global _status_cache
    if _status_cache is not None:
        return _status_cache
    sg = get_sg()
    schema = sg.schema_field_read("Version", "sg_status_list")
    valid_codes = (
        schema.get("sg_status_list", {})
              .get("properties", {})
              .get("valid_values", {})
              .get("value", [])
    ) or ["rev", "vwd", "na", "ip", "apr", "fail", "wtg"]
    code_to_name = {s["code"]: s["name"] for s in sg.find("Status", [], ["code", "name"])}
    _status_cache = {c: code_to_name.get(c, c) for c in valid_codes}
    return _status_cache
