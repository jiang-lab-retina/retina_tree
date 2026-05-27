"""Home page: view live retina lineage trees."""

from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components

from retina_tree.tree_html import estimate_card_height, render_tree_card_html
from retina_tree.ui import (
    configure_page,
    ensure_dataset_loaded,
    inject_apple_theme,
    render_box_filter,
    render_pending_badge,
    render_status_banner,
    render_view_toolbar,
)


def render_compact_header() -> None:
    dataset = st.session_state.dataset
    title = dataset["title"] if dataset else "Retina Trees"

    left, mid, right = st.columns([3, 1, 1])
    with left:
        st.markdown(
            f"""
            <div class="apple-hero" style="margin-bottom:0.5rem;">
              <h1 style="font-size:1.75rem;margin-bottom:0.15rem;">{title}</h1>
            </div>
            """,
            unsafe_allow_html=True,
        )
        render_pending_badge()
    with mid:
        st.page_link("pages/Edit_Data.py", label="Edit data", icon="✏️", use_container_width=True)
    with right:
        st.page_link("pages/Admin_Review.py", label="Admin", icon="🛡️", use_container_width=True)


def render_trees(filter_box_id: str | None = None) -> None:
    dataset = st.session_state.dataset
    if not dataset or not dataset.get("boxes"):
        st.warning("No trees loaded.")
        return

    view_mode = st.session_state.view_mode
    current_box_id = st.session_state.current_box_id
    boxes = dataset["boxes"]

    if filter_box_id:
        boxes = [box for box in boxes if box["id"] == filter_box_id]

    for box in boxes:
        card_html = render_tree_card_html(
            box,
            current_box_id=current_box_id,
            view_mode=view_mode,
            card_id=box["id"],
        )
        height = estimate_card_height(box)
        components.html(card_html, height=height, scrolling=True)


def main() -> None:
    configure_page(title="Retina Trees", icon="🌳")
    inject_apple_theme()
    ensure_dataset_loaded()

    render_compact_header()

    filter_box_id = render_box_filter()
    render_trees(filter_box_id)

    render_view_toolbar()
    render_status_banner()


if __name__ == "__main__":
    main()
