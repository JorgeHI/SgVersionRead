# Usage

## Loading a version manually

1. Create node: **Nodes → ShotGrid → SGVersionRead** (or `Tab` search).
2. In the **SG Version Read** tab:
   - Set **Project**, **Sequence**, **Shot** (or rely on env-var defaults).
   - Optionally set **Status Filter** (default `rev,vwd`).
3. Click **Refresh** — the **Entity / Task** list populates.
4. Select a task, click **Load Latest**.

The node loads the latest version matching your filters. The internal Read node
is updated automatically.

## Node color

| Color  | Meaning                                            |
|--------|----------------------------------------------------|
| Green  | Loaded version is the latest for the current filter|
| Red    | A newer version exists                             |
| Black  | No version loaded                                  |

## Dropping a ShotGrid URL

Copy a ShotGrid version URL (`/detail/Version/<id>`) and paste / drop it onto the
Nuke node graph. A new SGVersionRead is created and the version is loaded immediately.

Supported URL formats:

```
https://studio.shotgunstudio.com/detail/Version/12345
https://studio.shotgridglobal.com/detail/Version/12345
```

## Open in Browser

Click **Open in Browser** in the Version tab to open the current version's ShotGrid
page in the default browser.

## Auto version check

Enable **Auto Version Check** in the Options tab.  A single background thread
(started when Nuke launches) polls ShotGrid every **Check Interval** seconds.

When a newer version is detected, a dialog asks if you want to load it:
- If accepted, a **new SGVersionRead** is created with the latest version.
- Downstream nodes are re-wired to the new node.
- The old node stays in the graph for reference / comparison.

## Environment variable defaults

If the following env vars are set, new nodes auto-fill the context knobs:

| Env var       | Knob     |
|---------------|----------|
| `SG_PROJECT`  | Project  |
| `SG_SEQUENCE` | Sequence |
| `SG_SHOT`     | Shot     |
| `SG_TASK`     | Task     |
