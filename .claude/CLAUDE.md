# SGVersionRead — project context

Nuke gizmo that loads ShotGrid / Flow Production Tracking versions.

## Stack

- **Nuke** — host application (Python 3.x, nuke / nukescripts modules)
- **shotgun_api3** — official ShotGrid REST API client
- **Python** — 3.7+ compatible (Nuke's embedded Python)

## Key design decisions

- `gizmo/SGVersionRead.gizmo` is the **source of truth**. The `.nk` is generated.
- All Nuke node logic lives in `python/SGVersionRead/node_handler.py`.
- A single background thread (`version_checker.py`) serves all nodes in the session.
- SG connection is a thread-safe singleton (`sg_client.py`).
- Colors: green (`0x4BBF51FF`) = latest, red (`0xBF4F4FFF`) = outdated, 0 = no version.
- `file_path` Group knob drives the internal Read via TCL expression `[value parent.file_path]`.

## Building the .nk

```bash
python scripts/build_nk.py
```

This zips all `.py` files under `python/SGVersionRead/`, base64-encodes the zip,
and patches it into the gizmo's `onCreate` callback as a self-extracting bootstrap.

## Environment variables (see constants.py)

`SG_URL`, `SG_SCRIPT_NAME`, `SG_API_KEY`, `SG_PROJECT`, `SG_SEQUENCE`, `SG_SHOT`, `SG_TASK`

## Nuke integration

Add `nuke/` to `NUKE_PATH` so Nuke auto-loads `init.py` and `menu.py`.
Add `gizmo/` to `NUKE_PATH` so the `.gizmo` is registered as a node type.
Add `python/` to `NUKE_PATH` (or `sys.path`) for the Python module.
