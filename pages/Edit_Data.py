"""Edit page: modify nodes, links, and export JSON."""

from __future__ import annotations

import streamlit as st

from retina_tree.ui import (
    configure_page,
    ensure_dataset_loaded,
    inject_apple_theme,
    render_editor_page,
    render_page_header,
)


configure_page(title="Edit Data · Retina Trees", icon="✏️")
inject_apple_theme()
ensure_dataset_loaded()

render_page_header(
    subtitle="Add or remove nodes and parent → child links. Changes stay in memory until you download JSON."
)
render_editor_page()
