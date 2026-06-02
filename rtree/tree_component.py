"""Bidirectional Streamlit component for click-to-edit tree rendering."""

from __future__ import annotations

from pathlib import Path

import streamlit.components.v1 as components

_COMPONENT_DIR = Path(__file__).parent / "tree_component"
_editable_tree = components.declare_component(
    "editable_tree",
    path=str(_COMPONENT_DIR),
)


def editable_tree_component(
    tree_html: str,
    *,
    edit_mode: bool = False,
    tree_height: int = 600,
    key: str | None = None,
) -> dict | None:
    """Render tree cards.

    In edit mode the user can click any node label to rename it.
    Returns ``{"action": "save", "boxId": ..., "nodeId": ..., "newLabel": ...}``
    when the user confirms an edit, otherwise ``None``.
    """
    return _editable_tree(
        treeHtml=tree_html,
        editMode=edit_mode,
        treeHeight=tree_height,
        key=key,
        default=None,
    )
