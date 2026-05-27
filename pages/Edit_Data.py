"""Propose edits (requires Google sign-in; admin approval required to publish)."""

from __future__ import annotations

from retina_tree.ui import (
    configure_page,
    ensure_dataset_loaded,
    inject_apple_theme,
    render_editor_page,
    render_page_header,
)

configure_page(title="Propose Edit · Retina Trees", icon="✏️")
inject_apple_theme()
ensure_dataset_loaded()

render_page_header(
    subtitle="Submit changes to nodes or links. Each edit is tracked and must be approved before it appears on the public trees."
)
render_editor_page()
