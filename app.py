"""Home page: view live retina lineage trees."""

from __future__ import annotations

import site_setup  # noqa: F401

import streamlit as st

from rtree.streamlit_render import render_html_fragment, streamlit_supports_tree_html
from rtree.tree_html import estimate_trees_height, render_trees_html
from rtree.ui import (
    configure_page,
    ensure_dataset_loaded,
    inject_apple_theme,
    render_box_filter,
    render_home_landing,
    render_inline_name_editor,
    render_pending_badge,
    render_person_search,
    render_site_footer,
    render_status_banner,
    render_trees_section_intro,
    render_view_toolbar,
)


def render_home_nav() -> None:
    render_pending_badge()
    nav1, nav2 = st.columns(2)
    with nav1:
        st.page_link("pages/Edit_Data.py", label="Edit dataset", icon="✏️", use_container_width=True)
    with nav2:
        st.page_link("pages/Admin_Review.py", label="Admin", icon="🛡️", use_container_width=True)


def render_trees(
    filter_box_id: str | None = None,
    *,
    focus_node_id: str | None = None,
    focus_box_id: str | None = None,
    highlight_node_ids: set[str] | None = None,
) -> None:
    dataset = st.session_state.dataset
    if not dataset or not dataset.get("boxes"):
        st.warning("No trees loaded.")
        return

    view_mode = st.session_state.view_mode
    current_box_id = st.session_state.current_box_id
    boxes = dataset["boxes"]

    if filter_box_id:
        boxes = [box for box in boxes if box["id"] == filter_box_id]

    if not streamlit_supports_tree_html():
        st.warning(
            "Interactive trees need **Streamlit 1.52 or newer**. "
            "Redeploy after upgrading `requirements.txt` on Streamlit Cloud."
        )

    trees_html = render_trees_html(
        boxes,
        current_box_id=current_box_id,
        view_mode=view_mode,
        focus_node_id=focus_node_id,
        focus_box_id=focus_box_id,
        highlight_node_ids=highlight_node_ids,
    )
    render_html_fragment(
        trees_html,
        height=estimate_trees_height(boxes, view_mode),
    )


def main() -> None:
    try:
        configure_page(title="Retina Tree")
        inject_apple_theme()
        ensure_dataset_loaded()

        render_home_landing()

        render_home_nav()
        render_inline_name_editor()
        search_box_id, search_focus_id, search_highlights = render_person_search()
        filter_box_id = render_box_filter(search_box_id=search_box_id)

        render_trees_section_intro()
        render_view_toolbar()
        render_trees(
            filter_box_id,
            focus_node_id=search_focus_id,
            focus_box_id=search_box_id,
            highlight_node_ids=search_highlights or None,
        )

        render_status_banner()
        render_site_footer()
    except Exception as exc:
        st.error("The app hit an error while loading. Details below.")
        st.exception(exc)


if __name__ == "__main__":
    main()
