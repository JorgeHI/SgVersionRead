import re
import traceback

from .constants import SG_VERSION_URL_PATTERNS
from .logger import getLogger

logger = getLogger(__name__)


def _extract_version_id(text):
    for pattern in SG_VERSION_URL_PATTERNS:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return int(m.group(1))
    return None


def handle_drop(mime_type, text):
    """nukescripts drop-data callback. Return True if SG Version URL handled."""
    if isinstance(text, bytes):
        text = text.decode("utf-8", errors="ignore")
    version_id = _extract_version_id(text.strip())
    if version_id is None:
        return None

    try:
        from .node_handler import create_node, load_version_from_id
        node = create_node()
        if node:
            load_version_from_id(node, version_id)
        return True
    except Exception:
        logger.warning("drop handler failed:\n%s", traceback.format_exc())
        return None
