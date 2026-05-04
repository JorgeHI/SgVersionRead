# SGVersionRead
![Static Badge](https://img.shields.io/badge/DCC-Nuke-yellow?style=flat)
![Static Badge](https://img.shields.io/badge/Python-grey?style=flat&logo=python&logoSize=auto)
![Static Badge](https://img.shields.io/badge/Tool-Nuke%20Gizmo-lightgrey?logo=nuke&logoColor=yellow)
![Static Badge](https://img.shields.io/badge/ShotGrid-Flow%20Production%20Tracking-green?style=flat)
![GitHub Release Date](https://img.shields.io/github/release-date/JorgeHI/SgVersionRead)

Nuke gizmo for loading ShotGrid / Flow Production Tracking versions directly into the node graph.

## Features

- Browse projects, sequences, shots and tasks from ShotGrid
- Filter versions by status (e.g. `rev`, `vwd`, `na`)
- Always loads the **latest** version (sorted by name, ascending)
- Paste a ShotGrid version URL onto the node graph → gizmo auto-created and loaded
- Auto-sets project / sequence / shot / task from environment variables
- Periodic background version checks (single shared thread, configurable interval)
- Node turns **green** when the loaded version is the latest; **red** when a newer one exists
- **Open in Browser** button launches the ShotGrid version page

## Installation

See [doc/installation.md](doc/installation.md).

## Usage

See [doc/usage.md](doc/usage.md).

## Structure

```
gizmo/      SGVersionRead.gizmo   — main gizmo (requires Python module on path)
            SGVersionRead.nk      — self-contained build (Python embedded)
python/     SGVersionRead/        — Python module
nuke/       init.py               — add to NUKE_PATH
            menu.py               — add to NUKE_PATH
scripts/    build_nk.py           — generate SGVersionRead.nk from gizmo + module
doc/        usage.md  installation.md
requirements.txt
```

## Environment Variables

| Variable         | Purpose                    |
|------------------|----------------------------|
| `SG_URL`         | ShotGrid site URL          |
| `SG_SCRIPT_NAME` | API script name            |
| `SG_API_KEY`     | API key for the script     |
| `SG_PROJECT`     | Default project name       |
| `SG_SEQUENCE`    | Default sequence code      |
| `SG_SHOT`        | Default shot code          |
| `SG_TASK`        | Default task name          |

## Build standalone .nk

```bash
python scripts/build_nk.py
```

## Supported Versions

![Static Badge](https://img.shields.io/badge/Nuke-%3E%3D13.0-yellow?style=flat&logo=nuke&logoColor=yellow&logoSize=auto)
![Static Badge](https://img.shields.io/badge/Nuke%20Licence-Commercial-yellow?logo=Nuke&logoColor=yellow)
![Static Badge](https://img.shields.io/badge/Python-%3E%3D3.7-blue?style=flat&logo=python&logoSize=auto)

## Author

- [Linkedin](https://www.linkedin.com/in/jorgehi-vfx/)
