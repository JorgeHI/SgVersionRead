import logging

dev_mode = False
logging_level = logging.DEBUG if dev_mode else logging.WARNING

# ShotGrid credential env var names
SG_URL = "SG_URL"
SG_SCRIPT_NAME = "SG_SCRIPT_NAME"
SG_API_KEY = "SG_API_KEY"

# Context env var names
SG_PROJECT = "SG_PROJECT"
SG_SEQUENCE = "SG_SEQUENCE"
SG_SHOT = "SG_SHOT"
SG_TASK = "SG_TASK"

# Version check defaults
DEFAULT_CHECK_INTERVAL = 300  # seconds

# All known SG version status codes (displayed in filter UI)
VERSION_STATUS_CODES = ["rev", "vwd", "na", "ip", "apr", "fail", "wtg"]

# Node tile colors — Nuke RGBA packed uint32 (R<<24 | G<<16 | B<<8 | A)
COLOR_LATEST   = 0x4BBF51FF   # green  — version is latest
COLOR_OUTDATED = 0xBF4F4FFF   # red    — newer version available
COLOR_DEFAULT  = 0x00000000   # black  — no version loaded

# ShotGrid URL patterns for version pages
SG_VERSION_URL_PATTERNS = [
    r"https?://[^/]+\.shotgunstudio\.com/detail/Version/(\d+)",
    r"https?://[^/]+\.shotgridglobal\.com/detail/Version/(\d+)",
    r"https?://[^/]+/detail/Version/(\d+)",
]
