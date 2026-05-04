import os
import sys
import nuke

# ── path setup ────────────────────────────────────────────────────────────────
_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.normpath(os.path.join(_here, ".."))

# Local pip deps installed via: scripts/install_deps.sh
_deps = os.path.join(_root, ".deps")
if os.path.isdir(_deps) and _deps not in sys.path:
    sys.path.insert(0, _deps)

# pluginAddPath adds to both nuke plugin path and sys.path
nuke.pluginAddPath(os.path.join(_root, "python"))
nuke.pluginAddPath(os.path.join(_root, "gizmo"))

# ── URL drop handler ──────────────────────────────────────────────────────────
try:
    from SGVersionRead.url_handler import handle_drop
    nuke.addDropDataCallback(handle_drop)
except Exception as _e:
    nuke.warning(f"SGVersionRead: could not register URL drop handler: {_e}")

# ── global version checker thread (one thread for all nodes) ──────────────────
try:
    from SGVersionRead.version_checker import start
    start()
except Exception as _e:
    nuke.warning(f"SGVersionRead: could not start version checker thread: {_e}")
