"""Add or modify a person and their parent / child relationships.

Each field can be picked from a dropdown of existing people or typed in
directly. Typing filters the list to partial matches; an unrecognized name
creates a new person. All changes go to the live working copy and await
admin approval.
"""

from __future__ import annotations

import site_setup  # noqa: F401

import streamlit as st

from rtree.data_utils import (
    add_link,
    find_box_by_title,
    get_current_box,
    get_or_create_box,
    get_or_create_node,
)
from rtree.ui import (
    configure_page,
    ensure_dataset_loaded,
    inject_apple_theme,
    persist_working_dataset,
    render_page_header,
    render_pending_badge,
    render_site_footer,
    render_status_banner,
    set_status,
)

configure_page(title="Add / Modify · Retina Tree")
inject_apple_theme()
ensure_dataset_loaded()

render_page_header(
    subtitle="Add a person or a relationship. Pick from existing people or type a new name; "
    "matches appear as you type. Changes await admin approval."
)

top_left, top_right = st.columns([3, 1])
with top_left:
    st.page_link("app.py", label="← Back to trees", icon="🌳")
with top_right:
    st.page_link("pages/Admin_Review.py", label="Admin review", icon="🛡️", use_container_width=True)

st.info(
    "Use the dropdowns to **select an existing person** or **type a new name**. "
    "Parent and Child are optional — fill in whichever relationships you want to record."
)
render_pending_badge()

dataset = st.session_state.dataset
if not dataset or not dataset.get("boxes"):
    st.warning("No dataset loaded.")
    st.stop()

boxes = dataset["boxes"]
box_titles = [b["title"] for b in boxes]

current_box = get_current_box(dataset, st.session_state.current_box_id)
default_index = box_titles.index(current_box["title"]) if current_box else 0

selected_title = st.selectbox(
    "Tree",
    options=box_titles,
    index=default_index,
    accept_new_options=True,
    help="Choose a tree, or type a new title to start a new one.",
    key="am_box",
)

# People options come from the matched existing box (empty for a brand-new tree).
preview_box = find_box_by_title(dataset, selected_title)
people = sorted(
    ({n["label"] for n in preview_box["nodes"]} if preview_box else set()),
    key=str.lower,
)

st.caption(
    f"{len(people)} person{'s' if len(people) != 1 else ''} in this tree."
    if preview_box
    else "New tree — add the first person below."
)

name = st.selectbox(
    "Name",
    options=people,
    index=None,
    accept_new_options=True,
    placeholder="Select an existing person or type a new name",
    key="am_name",
)

col_parent, col_child = st.columns(2)
with col_parent:
    parent = st.selectbox(
        "Parent (optional)",
        options=people,
        index=None,
        accept_new_options=True,
        placeholder="Select or type a parent",
        key="am_parent",
    )
with col_child:
    child = st.selectbox(
        "Child (optional)",
        options=people,
        index=None,
        accept_new_options=True,
        placeholder="Select or type a child",
        key="am_child",
    )

if st.button("Save", type="primary", use_container_width=True, key="am_save"):
    clean_name = (name or "").strip()
    clean_parent = (parent or "").strip()
    clean_child = (child or "").strip()

    if not clean_name:
        set_status("Enter a name before saving.", "error")
    else:
        box = get_or_create_box(dataset, selected_title)
        name_id = get_or_create_node(box, clean_name)

        added_links = 0
        warnings: list[str] = []

        if clean_parent:
            parent_id = get_or_create_node(box, clean_parent)
            if parent_id == name_id:
                warnings.append("Parent cannot be the same person as Name.")
            elif add_link(box, parent_id, name_id):
                added_links += 1
            else:
                warnings.append(f"Link {clean_parent} → {clean_name} already exists.")

        if clean_child:
            child_id = get_or_create_node(box, clean_child)
            if child_id == name_id:
                warnings.append("Child cannot be the same person as Name.")
            elif add_link(box, name_id, child_id):
                added_links += 1
            else:
                warnings.append(f"Link {clean_name} → {clean_child} already exists.")

        persist_working_dataset()
        st.session_state.current_box_id = box["id"]

        msg = f'Saved "{clean_name}" in "{box["title"]}"'
        if added_links:
            msg += f" with {added_links} relationship{'s' if added_links != 1 else ''}"
        msg += " \u2014 awaiting admin approval."
        if warnings:
            msg += " Note: " + " ".join(warnings)
        set_status(msg, "warning" if warnings else "success")
        st.rerun()

render_status_banner()
render_site_footer()
