import os
import threading
from .constants import SG_URL, SG_SCRIPT_NAME, SG_API_KEY

_local = threading.local()


def get_sg():
    """Return a thread-local Shotgun instance. Each thread gets its own connection."""
    if getattr(_local, "sg", None) is not None:
        return _local.sg
    try:
        import shotgun_api3
    except ImportError:
        raise ImportError(
            "shotgun_api3 not installed. Run: pip install shotgun_api3"
        )
    url = os.environ.get(SG_URL)
    script_name = os.environ.get(SG_SCRIPT_NAME)
    api_key = os.environ.get(SG_API_KEY)
    if not url:
        raise EnvironmentError(f"{SG_URL} env var not set")
    if not script_name:
        raise EnvironmentError(f"{SG_SCRIPT_NAME} env var not set")
    if not api_key:
        raise EnvironmentError(f"{SG_API_KEY} env var not set")
    _local.sg = shotgun_api3.Shotgun(url, script_name=script_name, api_key=api_key)
    return _local.sg


def reset():
    """Clear this thread's connection (e.g. after credential change)."""
    _local.sg = None
