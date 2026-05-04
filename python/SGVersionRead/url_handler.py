import re
import nuke
from .constants import SG_VERSION_URL_PATTERNS
from .logger import getLogger

logger = getLogger(__name__)


def _extract_version_id(text):
    for pattern in SG_VERSION_URL_PATTERNS:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return int(m.group(1))
    return None


def handle_drop(mime_type, data):
    """
    Nuke drop-data callback.  Register once with nuke.addDropDataCallback().
    Returns True if the drop was handled, None otherwise.
    """
    if mime_type not in ("text/plain", "text/uri-list"):
        return None

    text = data.strip() if isinstance(data, str) else data.decode("utf-8", errors="ignore").strip()
    version_id = _extract_version_id(text)
    if version_id is None:
        return None

    try:
        from .node_handler import create_node, load_version_from_id
        node = create_node()
        if node:
            load_version_from_id(node, version_id)
        return True
    except Exception as e:
        logger.warning(str(e))
        return None
