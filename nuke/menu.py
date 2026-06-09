import nuke
import nukescripts

# ── URL drop handler (GUI only) ───────────────────────────────────────────────
try:
    from SGVersionRead.url_handler import handle_drop
    nukescripts.addDropDataCallback(handle_drop)
except Exception as _e:
    nuke.warning(f"SGVersionRead: could not register URL drop handler: {_e}")


# ── Nodes > Image > SGVersionRead ─────────────────────────────────────────────
try:
    image_menu = nuke.menu("Nodes").findItem("Image")
    image_menu.addCommand(
        "SGVersionRead",
        "import SGVersionRead.node_handler as _h; _h.create_node()",
        icon="Read.png",
        index=1,
    )
except Exception as _e:
    nuke.warning(f"SGVersionRead: could not add menu entry: {_e}")
