import os
import re
import threading
import nuke
import nukescripts

from . import version_manager as vm
from .logger import getLogger
from .constants import (
    SG_PROJECT, SG_SEQUENCE, SG_SHOT, SG_TASK, SG_URL,
    COLOR_LATEST, COLOR_OUTDATED, COLOR_DEFAULT,
    VERSION_STATUS_CODES,
)

logger = getLogger(__name__)

# Tracks nodes running _cascade_init so knob_changed won't re-trigger the cascade.
# Set ops are atomic under CPython GIL — safe across threads.
_cascading: set = set()


# ── helpers ──────────────────────────────────────────────────────────────────

def _status_list(node):
    val = node["status_filter"].value().strip()
    if not val or val == "any":
        return None
    m = re.search(r"\(([^)]+)\)$", val)
    return [m.group(1) if m else val]


def _task_id(node):
    v = int(node["loaded_task_id"].value())
    return v if v != 0 else None


def _parse_task_id(label):
    m = re.search(r"\(id:(\d+)\)", label)
    return int(m.group(1)) if m else None


# ── node creation ─────────────────────────────────────────────────────────────

# Knob definition stamped onto a fresh Read node via Node.readKnobs().
# Raw string preserves literal \n required by Nuke's knob-script syntax.
_KNOBS_SCRIPT = r'''knobChanged "import SGVersionRead.node_handler as _h\n_h.knob_changed(nuke.thisNode(), nuke.thisKnob())"
onCreate "import SGVersionRead.node_handler as _h\n_h.on_create(nuke.thisNode())"
label {[value version_name]}
tile_color 0
addUserKnob {20 sgvr_tab l "SG Version Read"}
addUserKnob {4 sg_project l Project M {"-- loading --"}}
addUserKnob {4 sg_sequence l Sequence M {"-- select project --"}}
addUserKnob {4 sg_shot l Shot M {"-- select sequence --"}}
addUserKnob {4 task l Task M {"-- select shot --"}}
addUserKnob {26 _sep0 l "" +STARTLINE}
addUserKnob {4 status_filter l Status M {"any"}}
addUserKnob {22 refresh_status_btn l "  ↻  " T "import SGVersionRead.node_handler as _h; _h.populate_status_filter(nuke.thisNode())" -STARTLINE}
addUserKnob {26 _sep1 l "" +STARTLINE}
addUserKnob {22 refresh_btn l Refresh T "import SGVersionRead.node_handler as _h; _h.refresh_all(nuke.thisNode())"}
addUserKnob {22 load_btn l "Load Latest" T "import SGVersionRead.node_handler as _h; _h.load_selected_version(nuke.thisNode())" -STARTLINE}
addUserKnob {26 _sep2 l "" +STARTLINE}
addUserKnob {6 enable_auto_check l "Auto Version Check" +STARTLINE}
enable_auto_check false
addUserKnob {3 check_interval l "Check Interval (sec)" -STARTLINE}
check_interval 300
addUserKnob {20 version_tab l Version}
addUserKnob {1 version_name l Version +READONLY}
version_name ""
addUserKnob {1 version_status l Status +READONLY}
version_status ""
addUserKnob {3 version_id l "Version ID" +READONLY}
version_id 0
addUserKnob {22 open_browser_btn l "Open in Browser" T "import SGVersionRead.node_handler as _h; _h.open_in_browser(nuke.thisNode())" +STARTLINE}
addUserKnob {3 loaded_task_id l "Task ID" +INVISIBLE +READONLY}
loaded_task_id 0
addUserKnob {3 loaded_project_id l "Project ID" +INVISIBLE +READONLY}
loaded_project_id 0
addUserKnob {3 loaded_sequence_id l "Sequence ID" +INVISIBLE +READONLY}
loaded_sequence_id 0
addUserKnob {3 loaded_shot_id l "Shot ID" +INVISIBLE +READONLY}
loaded_shot_id 0
addUserKnob {1 node_version l "Node Version" +INVISIBLE}
node_version "0.1.0"
'''


def create_node():
    """Build SGVersionRead from a fresh Read + stamped user knobs.

    Avoids nuke.nodePaste which collides with Nuke's drop-event state
    ("RuntimeError: Viewer1") and removes the need for an external .nk file.
    """
    n = nuke.createNode("Read", inpanel=False)
    if n is None:
        return None
    try:
        n.setName("SGVersionRead", uncollide=True)
    except Exception:
        pass
    n.readKnobs(_KNOBS_SCRIPT)
    # readKnobs only stores the onCreate string for future loads — fire it now.
    try:
        on_create(n)
    except Exception as e:
        logger.warning(str(e))
    return n


# ── public API ────────────────────────────────────────────────────────────────

def on_create(node=None):
    if node is None:
        node = nuke.thisNode()

    node["file"].setFlag(nuke.DISABLED)
    if not node["enable_auto_check"].value():
        node["check_interval"].setFlag(nuke.DISABLED)

    node["status_filter"].setValues(["any"] + VERSION_STATUS_CODES)

    threading.Thread(
        target=_cascade_init,
        args=(
            node.name(),
            os.environ.get(SG_PROJECT, ""),
            os.environ.get(SG_SEQUENCE, ""),
            os.environ.get(SG_SHOT, ""),
            os.environ.get(SG_TASK, ""),
        ),
        daemon=True,
    ).start()

    update_node_color(node)


def knob_changed(node=None, knob=None):
    if node is None:
        node = nuke.thisNode()
    if knob is None:
        knob = nuke.thisKnob()

    if node.name() in _cascading:
        return

    name = knob.name()
    val  = knob.value()

    if name == "enable_auto_check":
        if val:
            node["check_interval"].clearFlag(nuke.DISABLED)
        else:
            node["check_interval"].setFlag(nuke.DISABLED)

    elif name == "sg_project" and val and not val.startswith("--"):
        node["sg_sequence"].setValues(["-- loading --"])
        node["sg_shot"].setValues(["-- select sequence --"])
        node["task"].setValues(["-- select shot --"])
        threading.Thread(
            target=_bg_populate_sequences,
            args=(node.name(), val),
            daemon=True,
        ).start()

    elif name == "sg_sequence" and val and not val.startswith("--"):
        p_id = int(node["loaded_project_id"].value())
        if p_id:
            node["sg_shot"].setValues(["-- loading --"])
            node["task"].setValues(["-- select shot --"])
            threading.Thread(
                target=_bg_populate_shots,
                args=(node.name(), p_id, val),
                daemon=True,
            ).start()

    elif name == "sg_shot" and val and not val.startswith("--"):
        p_id = int(node["loaded_project_id"].value())
        if p_id:
            node["task"].setValues(["-- loading --"])
            threading.Thread(
                target=_bg_populate_tasks,
                args=(node.name(), p_id, val),
                daemon=True,
            ).start()


def refresh_all(node):
    """Re-populate all combos keeping current selections. Called from Refresh button."""
    def _cur(k):
        v = node[k].value()
        return v if v and not v.startswith("--") else ""

    cur_project  = _cur("sg_project")
    cur_seq      = _cur("sg_sequence")
    cur_shot     = _cur("sg_shot")
    cur_task_lbl = _cur("task")
    cur_task     = re.sub(r"\s*\(id:\d+\)$", "", cur_task_lbl) if cur_task_lbl else ""

    node["sg_project"].setValues(["-- loading --"])
    node["sg_sequence"].setValues(["-- loading --"])
    node["sg_shot"].setValues(["-- loading --"])
    node["task"].setValues(["-- loading --"])

    threading.Thread(
        target=_cascade_init,
        args=(node.name(), cur_project, cur_seq, cur_shot, cur_task),
        daemon=True,
    ).start()


def populate_status_filter(node):
    """Fetch valid Version statuses from SG and update the status combo."""
    node_name = node.name()
    threading.Thread(
        target=_bg_populate_statuses,
        args=(node_name, node["status_filter"].value()),
        daemon=True,
    ).start()


def load_selected_version(node):
    try:
        sel = node["task"].value()
        task_id = _parse_task_id(sel)
        if task_id is None:
            nuke.message("SGVersionRead: select a valid task first")
            return
        version = vm.get_latest_version(task_id=task_id, status_list=_status_list(node))
        if version is None:
            nuke.message("SGVersionRead: no versions found for this task / filter")
            return
        _apply_version(node, version, task_id=task_id)
    except Exception as e:
        logger.warning(str(e))


def load_version_from_id(node, version_id):
    try:
        version = vm.get_version_by_id(version_id)
        if version is None:
            logger.warning(f"version {version_id} not found in SG")
            return
        tid = version["sg_task"]["id"] if version.get("sg_task") else None
        _apply_version(node, version, task_id=tid)
    except Exception as e:
        logger.warning(str(e))


def _apply_version(node, version, task_id=None):
    path = vm.get_version_file_path(version)
    node["version_name"].setValue(version["code"])
    node["version_id"].setValue(version["id"])
    code = version.get("sg_status_list", "")
    statuses = vm._status_cache
    if statuses:
        name = statuses.get(code, code)
        status_display = f"{name} ({code})" if name != code else code
    else:
        status_display = code
    node["version_status"].setValue(status_display)
    first = version.get("sg_first_frame")
    last = version.get("sg_last_frame")
    if first is not None and last is not None:
        node["file"].fromUserText("{} {}-{}".format(path, int(first), int(last)))
    else:
        node["file"].fromUserText(path)
    if task_id:
        node["loaded_task_id"].setValue(task_id)
    update_node_color(node)


def update_node_color(node):
    try:
        vid = int(node["version_id"].value())
        if vid == 0:
            node["tile_color"].setValue(COLOR_DEFAULT)
            return
        latest = vm.is_latest_version(
            vid, task_id=_task_id(node), status_list=_status_list(node)
        )
        node["tile_color"].setValue(COLOR_LATEST if latest else COLOR_OUTDATED)
    except Exception as e:
        logger.warning(str(e))


def open_in_browser(node):
    try:
        vid = int(node["version_id"].value())
        if vid == 0:
            nuke.message("SGVersionRead: no version loaded")
            return
        base = os.environ.get(SG_URL, "").rstrip("/")
        if not base:
            nuke.message(f"SGVersionRead: {SG_URL} env var not set")
            return
        nukescripts.start(f"{base}/detail/Version/{vid}")
    except Exception as e:
        logger.warning(str(e))


# ── background cascade functions ──────────────────────────────────────────────

def _cascade_init(node_name, env_project, env_seq, env_shot, env_task):
    """Full cascade populate with optional env-default auto-selection."""
    _cascading.add(node_name)
    try:
        # ── projects ──────────────────────────────────────────────────────────
        projects = vm.get_projects()
        p_labels = [p["name"] for p in projects] or ["-- no projects --"]
        p_match  = p_labels.index(env_project) if env_project in p_labels else None
        p_id     = projects[p_match]["id"] if p_match is not None else None

        def _set_projects(lbls=p_labels, idx=p_match):
            n = nuke.toNode(node_name)
            if not n:
                return
            n["sg_project"].setValues(lbls)
            if idx is not None:
                n["sg_project"].setValue(idx)
        nuke.executeInMainThread(_set_projects)

        if p_id is None:
            return

        # ── sequences ─────────────────────────────────────────────────────────
        seqs     = vm.get_sequences(p_id)
        s_labels = [s["code"] for s in seqs] or ["-- no sequences --"]
        s_match  = s_labels.index(env_seq) if env_seq in s_labels else None
        s_id     = seqs[s_match]["id"] if s_match is not None else None

        def _set_seqs(lbls=s_labels, idx=s_match, pid=p_id):
            n = nuke.toNode(node_name)
            if not n:
                return
            n["loaded_project_id"].setValue(pid)
            n["sg_sequence"].setValues(lbls)
            if idx is not None:
                n["sg_sequence"].setValue(idx)
            n["sg_shot"].setValues(["-- select sequence --"])
            n["task"].setValues(["-- select shot --"])
        nuke.executeInMainThread(_set_seqs)

        if s_id is None:
            return

        # ── shots ─────────────────────────────────────────────────────────────
        shots     = vm.get_shots(p_id, sequence_id=s_id)
        sh_labels = [s["code"] for s in shots] or ["-- no shots --"]
        sh_match  = sh_labels.index(env_shot) if env_shot in sh_labels else None
        sh_id     = shots[sh_match]["id"] if sh_match is not None else None

        def _set_shots(lbls=sh_labels, idx=sh_match, sid=s_id):
            n = nuke.toNode(node_name)
            if not n:
                return
            n["loaded_sequence_id"].setValue(sid)
            n["sg_shot"].setValues(lbls)
            if idx is not None:
                n["sg_shot"].setValue(idx)
            n["task"].setValues(["-- select shot --"])
        nuke.executeInMainThread(_set_shots)

        if sh_id is None:
            return

        # ── tasks ─────────────────────────────────────────────────────────────
        tasks    = vm.get_tasks(p_id, shot_id=sh_id)
        t_labels = [f"{t['content']} (id:{t['id']})" for t in tasks] or ["-- no tasks --"]
        t_match  = next(
            (i for i, t in enumerate(tasks) if t["content"] == env_task), None
        ) if env_task else None

        def _set_tasks(lbls=t_labels, idx=t_match, shid=sh_id):
            n = nuke.toNode(node_name)
            if not n:
                return
            n["loaded_shot_id"].setValue(shid)
            n["task"].setValues(lbls)
            if idx is not None:
                n["task"].setValue(idx)
        nuke.executeInMainThread(_set_tasks)

    except Exception as e:
        logger.warning(str(e))
        def _on_error():
            n = nuke.toNode(node_name)
            if not n:
                return
            for k in ("sg_project", "sg_sequence", "sg_shot", "task"):
                try:
                    if n[k].value().startswith("-- loading"):
                        n[k].setValues(["-- SG unavailable --"])
                except Exception:
                    pass
        nuke.executeInMainThread(_on_error)
    finally:
        _cascading.discard(node_name)


def _bg_populate_sequences(node_name, project_name):
    try:
        project  = vm.find_project_by_name(project_name)
        if not project:
            nuke.executeInMainThread(
                lambda: nuke.toNode(node_name) and
                        nuke.toNode(node_name)["sg_sequence"].setValues(["-- project not found --"])
            )
            return
        p_id     = project["id"]
        seqs     = vm.get_sequences(p_id)
        s_labels = [s["code"] for s in seqs] or ["-- no sequences --"]

        def _update(lbls=s_labels, pid=p_id):
            n = nuke.toNode(node_name)
            if not n:
                return
            n["loaded_project_id"].setValue(pid)
            n["sg_sequence"].setValues(lbls)
            n["sg_shot"].setValues(["-- select sequence --"])
            n["task"].setValues(["-- select shot --"])
        nuke.executeInMainThread(_update)
    except Exception as e:
        logger.warning(str(e))


def _bg_populate_shots(node_name, project_id, seq_name):
    try:
        seq = vm.find_sequence_by_code(seq_name, project_id)
        if not seq:
            nuke.executeInMainThread(
                lambda: nuke.toNode(node_name) and
                        nuke.toNode(node_name)["sg_shot"].setValues(["-- sequence not found --"])
            )
            return
        s_id      = seq["id"]
        shots     = vm.get_shots(project_id, sequence_id=s_id)
        sh_labels = [s["code"] for s in shots] or ["-- no shots --"]

        def _update(lbls=sh_labels, sid=s_id):
            n = nuke.toNode(node_name)
            if not n:
                return
            n["loaded_sequence_id"].setValue(sid)
            n["sg_shot"].setValues(lbls)
            n["task"].setValues(["-- select shot --"])
        nuke.executeInMainThread(_update)
    except Exception as e:
        logger.warning(str(e))


def _bg_populate_tasks(node_name, project_id, shot_name):
    try:
        shot = vm.find_shot_by_code(shot_name, project_id)
        if not shot:
            nuke.executeInMainThread(
                lambda: nuke.toNode(node_name) and
                        nuke.toNode(node_name)["task"].setValues(["-- shot not found --"])
            )
            return
        sh_id    = shot["id"]
        tasks    = vm.get_tasks(project_id, shot_id=sh_id)
        t_labels = [f"{t['content']} (id:{t['id']})" for t in tasks] or ["-- no tasks --"]

        def _update(lbls=t_labels, shid=sh_id):
            n = nuke.toNode(node_name)
            if not n:
                return
            n["loaded_shot_id"].setValue(shid)
            n["task"].setValues(lbls)
        nuke.executeInMainThread(_update)
    except Exception as e:
        logger.warning(str(e))


def _bg_populate_statuses(node_name, current_val):
    try:
        statuses = vm.get_version_statuses()  # {code: name}
        labels = ["any"] + [f"{name} ({code})" for code, name in statuses.items()]

        m = re.search(r"\(([^)]+)\)$", current_val)
        current_code = m.group(1) if m else current_val

        def _update(lbls=labels, cur_code=current_code):
            n = nuke.toNode(node_name)
            if not n:
                return
            n["status_filter"].setValues(lbls)
            for i, lbl in enumerate(lbls):
                mm = re.search(r"\(([^)]+)\)$", lbl)
                if (mm and mm.group(1) == cur_code) or lbl == cur_code:
                    n["status_filter"].setValue(i)
                    break
        nuke.executeInMainThread(_update)
    except Exception as e:
        logger.warning(str(e))
