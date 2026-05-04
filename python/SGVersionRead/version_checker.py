"""
Single background thread that periodically checks all SGVersionRead nodes
for newer versions.  One thread for all nodes — started once from init.py.

Threading rules (Nuke dev guide):
  - nuke.* API calls must run on the main thread.
  - executeInMainThread / executeInMainThreadWithResult must NOT be called
    from the main thread (Nuke will hang).
  - Background thread: safe for pure Python and SG network calls only.
"""

import re
import threading
import nuke
from .constants import DEFAULT_CHECK_INTERVAL

_thread = None
_stop = threading.Event()
_lock = threading.Lock()


# ── main-thread helpers ───────────────────────────────────────────────────────

def _collect_snapshots():
    """
    Gather node state needed for version checks.
    Must be called on the main thread (via executeInMainThreadWithResult).
    Returns (interval, [snapshot_dict, ...]).
    """
    interval = DEFAULT_CHECK_INTERVAL
    snapshots = []
    try:
        for node in nuke.allNodes():
            try:
                if not (node.knob("version_id") and node.knob("enable_auto_check")):
                    continue
                # Read check interval from first eligible node
                if node.knob("check_interval"):
                    v = int(node["check_interval"].value())
                    if v > 0:
                        interval = v
                if not node["enable_auto_check"].value():
                    continue
                vid = int(node["version_id"].value())
                if vid == 0:
                    continue
                tid_val = int(node["loaded_task_id"].value())
                raw = node["status_filter"].value().strip()
                m = re.search(r"\(([^)]+)\)$", raw) if raw and raw != "any" else None
                status_code = m.group(1) if m else (raw if raw and raw != "any" else None)
                snapshots.append({
                    "name": node.name(),
                    "version_id": vid,
                    "task_id": tid_val if tid_val != 0 else None,
                    "status_list": [status_code] if status_code else None,
                })
            except Exception:
                pass
    except Exception:
        pass
    return interval, snapshots


def _on_update_found(node_name, new_version, task_id):
    """Show dialog and optionally create update node. Runs on main thread."""
    node = nuke.toNode(node_name)
    if node is None:
        return

    current = node["version_name"].value()
    new_name = new_version["code"]

    if not nuke.ask(
        f"SGVersionRead — new version available on '{node_name}'\n\n"
        f"Loaded : {current}\n"
        f"Latest : {new_name}\n\n"
        f"Create new SGVersionRead with latest version?"
    ):
        return

    _create_update_node(node, new_version, task_id)


def _create_update_node(old_node, new_version, task_id):
    """Create new node with new version, rewire downstream. Runs on main thread."""
    from .node_handler import create_node, _apply_version

    new_node = create_node()
    if new_node is None:
        return

    new_node.setXYpos(old_node.xpos() + 160, old_node.ypos())

    for k in ("sg_project", "sg_sequence", "sg_shot", "task",
              "status_filter", "enable_auto_check", "check_interval"):
        try:
            new_node[k].setValue(old_node[k].value())
        except Exception:
            pass

    _apply_version(new_node, new_version, task_id=task_id)

    for downstream in nuke.allNodes():
        for i in range(downstream.inputs()):
            if downstream.input(i) is old_node:
                downstream.setInput(i, new_node)


# ── background-thread worker ──────────────────────────────────────────────────

def _check_snapshots(snapshots):
    """SG queries — safe to run on background thread."""
    from . import version_manager as vm

    for snap in snapshots:
        try:
            latest = vm.get_latest_version(
                task_id=snap["task_id"],
                status_list=snap["status_list"],
            )
            if latest and latest["id"] != snap["version_id"]:
                new_ver = dict(latest)
                # Dispatch UI work back to main thread
                nuke.executeInMainThread(
                    _on_update_found,
                    args=(snap["name"], new_ver, snap["task_id"]),
                )
        except Exception:
            pass


def _loop():
    interval = DEFAULT_CHECK_INTERVAL
    while not _stop.is_set():
        _stop.wait(interval)
        if _stop.is_set():
            break
        try:
            # Collect node state on main thread, then query SG on this thread
            interval, snapshots = nuke.executeInMainThreadWithResult(_collect_snapshots)
            _check_snapshots(snapshots)
        except Exception:
            interval = DEFAULT_CHECK_INTERVAL


# ── public ────────────────────────────────────────────────────────────────────

def start():
    """Start the global checker thread (idempotent)."""
    global _thread
    with _lock:
        if _thread and _thread.is_alive():
            return
        _stop.clear()
        _thread = threading.Thread(
            target=_loop, name="SGVersionRead-Checker", daemon=True
        )
        _thread.start()


def stop():
    global _thread
    with _lock:
        if _thread is None:
            return
        _stop.set()
        _thread.join(timeout=5)
        _thread = None
