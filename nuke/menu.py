import os
import re
import nuke

try:
    _nk = next(
        (os.path.join(p, "SGVersionRead.nk") for p in nuke.pluginPath()
         if os.path.isfile(os.path.join(p, "SGVersionRead.nk"))),
        None,
    )
    if _nk:
        image_menu = nuke.menu("Nodes").findItem("Image")
        image_menu.addCommand(
            "SGVersionRead",
            f"nuke.nodePaste(r'{_nk}')",
            icon="Read.png",
            index=1,
        )
    else:
        nuke.warning("SGVersionRead: SGVersionRead.nk not found in plugin path")
except Exception as _e:
    nuke.warning(f"SGVersionRead: could not add menu entry: {_e}")


def _sg_paste():
    try:
        from PySide2.QtWidgets import QApplication
    except ImportError:
        from PySide6.QtWidgets import QApplication

    clipboard_text = QApplication.clipboard().text().strip()

    try:
        from SGVersionRead.constants import SG_VERSION_URL_PATTERNS
        for pattern in SG_VERSION_URL_PATTERNS:
            m = re.search(pattern, clipboard_text, re.IGNORECASE)
            if m:
                version_id = int(m.group(1))
                from SGVersionRead.node_handler import create_node, load_version_from_id
                node = create_node()
                if node:
                    load_version_from_id(node, version_id)
                return
    except Exception as _e:
        nuke.warning(f"SGVersionRead: paste handler error: {_e}")

    nuke.nodePaste("clipboard:")


try:
    nuke.menu("Nuke").findItem("Edit/Paste").setScript(_sg_paste)
except Exception as _e:
    nuke.warning(f"SGVersionRead: could not override paste: {_e}")
