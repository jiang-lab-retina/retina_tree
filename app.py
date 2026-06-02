"""Home page: view live retina lineage trees."""

from __future__ import annotations

import site_setup  # noqa: F401

from pathlib import Path

import streamlit as st

from rtree.streamlit_render import render_html_fragment, streamlit_supports_tree_html
from rtree.tree_html import estimate_trees_height, render_trees_html
from rtree.ui import (
    configure_page,
    ensure_dataset_loaded,
    inject_apple_theme,
    persist_working_dataset,
    render_box_filter,
    render_home_landing,
    render_inline_name_editor,
    render_pending_badge,
    render_person_search,
    render_site_footer,
    render_status_banner,
    render_trees_section_intro,
    render_view_toolbar,
    set_status,
)

_POSTER_PATH = Path(__file__).parent / "FASEB Poster 2026-6-10.pdf"


def render_home_nav() -> None:
    """Navigation buttons shown at the bottom of the home page."""
    render_pending_badge()
    nav1, nav2, nav3 = st.columns(3)
    with nav1:
        st.page_link("pages/Edit_Data.py", label="Edit dataset", icon="✏️", use_container_width=True)
    with nav2:
        st.page_link("pages/Add_Modify.py", label="Add/Modify", icon="➕", use_container_width=True)
    with nav3:
        st.page_link("pages/Admin_Review.py", label="Admin", icon="🛡️", use_container_width=True)


def render_poster_download() -> None:
    """Download button for the FASEB 2026 poster PDF, shown below the hero."""
    if not _POSTER_PATH.exists():
        return
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.download_button(
            label="📄 Poster at FASEB 2026",
            data=_POSTER_PATH.read_bytes(),
            file_name="FASEB_Poster_2026-6-10.pdf",
            mime="application/pdf",
            use_container_width=True,
        )


def _apply_node_rename(box_id: str, node_id: str, new_label: str) -> None:
    dataset = st.session_state.get("dataset")
    if not dataset:
        return
    for box in dataset.get("boxes", []):
        if box["id"] == box_id:
            for node in box.get("nodes", []):
                if node["id"] == node_id:
                    node["label"] = new_label
                    persist_working_dataset()
                    set_status(
                        f'Renamed "{node_id}" to "{new_label}" \u2014 awaiting admin approval.',
                        "success",
                    )
                    return
    set_status(f"Could not find node {node_id!r} in box {box_id!r}.", "error")


def _apply_box_title_rename(box_id: str, new_title: str) -> None:
    dataset = st.session_state.get("dataset")
    if not dataset:
        return
    for box in dataset.get("boxes", []):
        if box["id"] == box_id:
            old_title = box.get("title", box_id)
            box["title"] = new_title
            persist_working_dataset()
            set_status(
                f'Renamed tree "{old_title}" to "{new_title}" \u2014 awaiting admin approval.',
                "success",
            )
            return
    set_status(f"Could not find tree {box_id!r}.", "error")


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
    height = estimate_trees_height(boxes, view_mode)

    edit_mode = st.session_state.get("inline_edit_active", False)
    if edit_mode:
        # Lazy import so a missing/broken component never breaks the whole page.
        try:
            from rtree.tree_component import editable_tree_component
            result = editable_tree_component(
                trees_html,
                edit_mode=True,
                tree_height=height,
                key="editable_tree",
            )
            if result:
                action = result.get("action", "")
                if action == "save-node":
                    _apply_node_rename(result["boxId"], result["nodeId"], result["newLabel"])
                    st.rerun()
                elif action == "save-box-title":
                    _apply_box_title_rename(result["boxId"], result["newTitle"])
                    st.rerun()
        except Exception as exc:
            st.warning(f"Edit mode unavailable: {exc}")
            render_html_fragment(trees_html, height=height)
    else:
        render_html_fragment(trees_html, height=height)


def main() -> None:
    try:
        configure_page(title="Retina Tree")
        inject_apple_theme()
        ensure_dataset_loaded()

        render_home_landing()
        render_poster_download()

        edit_col, add_col = st.columns(2)
        with edit_col:
            render_inline_name_editor()
        with add_col:
            st.page_link(
                "pages/Add_Modify.py",
                label="➕ Add / Modify",
                icon=None,
                use_container_width=True,
            )
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
        st.divider()
        render_home_nav()
        render_site_footer()
    except Exception as exc:
        st.error("The app hit an error while loading. Details below.")
        st.exception(exc)


if __name__ == "__main__":
    main()
