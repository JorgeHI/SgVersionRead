# Installation

## 1. Install `shotgun_api3` (optional)

Skip this step if `shotgun_api3` is already available inside Nuke's Python environment.

Otherwise, install it into the local `.deps/` folder so the plugin can find it automatically:

```bash
# Recommended — uses the included script
bash scripts/install_deps.sh
```

Or manually:

```bash
pip install shotgun_api3 --target /path/to/SgVersionRead/.deps/
```

> `nuke/init.py` adds `.deps/` to `sys.path` automatically, so no extra setup is needed.

---

## 2. Add to NUKE_PATH

Add only the `nuke/` folder of this repository to your Nuke plugin path.
The `nuke/init.py` inside it registers the gizmo and Python module paths automatically.

### Option A — `~/.nuke/init.py`

```python
import nuke
nuke.pluginAddPath("/path/to/SgVersionRead/nuke")
```

### Option B — `NUKE_PATH` environment variable

```bash
export NUKE_PATH="/path/to/SgVersionRead/nuke:$NUKE_PATH"
```

---

## 3. Set environment variables

```bash
export SG_URL="https://mystudio.shotgunstudio.com"
export SG_SCRIPT_NAME="nuke_reader"
export SG_API_KEY="your_api_key_here"

# Optional — auto-populate context on node creation
export SG_PROJECT="MyProject"
export SG_SEQUENCE="SQ010"
export SG_SHOT="SQ010_0010"
export SG_TASK="comp"
```

> Variable names and default values can be customised in `python/SGVersionRead/constants.py`.

---

## 4. (Optional) Self-contained `.nk` build

To distribute a single `.nk` file with no external Python dependencies:

```bash
python scripts/build_nk.py
```

Place `gizmo/SGVersionRead.nk` anywhere and paste it into Nuke scripts directly.
SG credentials must still be provided via environment variables.
