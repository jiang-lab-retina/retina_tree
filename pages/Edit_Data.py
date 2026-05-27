"""Edit live tree data (changes appear immediately; admin makes them permanent)."""

from __future__ import annotations

import site_setup  # noqa: F401

from rtree.ui import (
    configure_page,
    ensure_dataset_loaded,
    inject_apple_theme,
    render_editor_page,
    render_page_header,
    render_site_footer,
)

configure_page(title="Edit Data · Retina Trees")
inject_apple_theme()
ensure_dataset_loaded()

render_page_header(
    subtitle="Edits update the live trees right away. The original dataset stays unchanged until an administrator accepts or rejects."
)
render_editor_page()
render_site_footer()
