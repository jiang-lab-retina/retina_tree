"""Add or modify a person and their relationships.

Sections:
  1. Tree  — pick existing or name a new one
  2. Person — name (autocomplete), PubMed link
  3. Relationships — parent(s) and child(ren)
"""

from __future__ import annotations

import site_setup  # noqa: F401

import streamlit as st

from rtree.branding import render_section_rule
from rtree.data_utils import (
    add_link,
    find_box_by_title,
    get_current_box,
    get_or_create_box,
    get_or_create_node,
    slugify_id,
    unique_node_id,
)
from rtree.streamlit_render import render_custom_html
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
    subtitle="Add a person or record a relationship. "
    "Start typing to search existing people; new names are created automatically."
)

top_left, top_right = st.columns([3, 1])
with top_left:
    st.page_link("app.py", label="← Back to trees", icon="🌳")
with top_right:
    st.page_link("pages/Admin_Review.py", label="Admin review", icon="🛡️", use_container_width=True)

render_pending_badge()

dataset = st.session_state.dataset
if not dataset or not dataset.get("boxes"):
    st.warning("No dataset loaded.")
    st.stop()

boxes = dataset["boxes"]
box_titles = [b["title"] for b in boxes]
current_box = get_current_box(dataset, st.session_state.current_box_id)

# ── 1. TREE ────────────────────────────────────────────────────────────────
render_custom_html(render_section_rule(label="Tree"))

tree_mode = st.radio(
    "Tree",
    options=["Select existing tree", "Create new tree"],
    horizontal=True,
    label_visibility="collapsed",
    key="am_tree_mode",
)

if tree_mode == "Select existing tree":
    box_index = box_titles.index(current_box["title"]) if current_box else 0
    selected_title = st.selectbox(
        "Existing tree",
        options=box_titles,
        index=box_index,
        key="am_existing_tree",
    )
    new_tree_name = ""
else:
    new_tree_name = st.text_input(
        "New tree name",
        placeholder="e.g. Harvard Retina Group",
        key="am_new_tree_name",
    )
    selected_title = new_tree_name.strip() or ""

preview_box = find_box_by_title(dataset, selected_title) if selected_title else None
people: list[str] = (
    sorted({n["label"] for n in preview_box["nodes"]}, key=str.lower)
    if preview_box
    else []
)

if preview_box:
    st.caption(f"{len(people)} person{'s' if len(people) != 1 else ''} already in this tree.")
elif tree_mode == "Create new tree" and selected_title:
    st.caption(f"New tree \"{selected_title}\" will be created.")

# ── 2. PERSON ──────────────────────────────────────────────────────────────
render_custom_html(render_section_rule(label="Person"))

col_name, col_pubmed = st.columns([2, 1])
with col_name:
    name = st.selectbox(
        "Name *",
        options=people,
        index=None,
        accept_new_options=True,
        placeholder="Select or type a name (required)",
        help="Pick an existing person from the list, or type a new name to add them.",
        key="am_name",
    )
with col_pubmed:
    pubmed = st.text_input(
        "PubMed link (optional)",
        placeholder="https://pubmed.ncbi.nlm.nih.gov/...",
        help="URL or PubMed ID linking to this person's paper.",
        key="am_pubmed",
    )

# ── 3. RELATIONSHIPS ───────────────────────────────────────────────────────
render_custom_html(render_section_rule(label="Relationships (optional)"))

st.caption(
    "Each field accepts one name. "
    "Pick from the dropdown or type a new name — they will be added to the tree automatically."
)

col_p1, col_p2 = st.columns(2)
with col_p1:
    parent1 = st.selectbox(
        "Parent 1",
        options=people,
        index=None,
        accept_new_options=True,
        placeholder="Select or type",
        key="am_parent1",
    )
with col_p2:
    parent2 = st.selectbox(
        "Parent 2",
        options=people,
        index=None,
        accept_new_options=True,
        placeholder="Select or type",
        key="am_parent2",
    )

col_c1, col_c2 = st.columns(2)
with col_c1:
    child1 = st.selectbox(
        "Child 1",
        options=people,
        index=None,
        accept_new_options=True,
        placeholder="Select or type",
        key="am_child1",
    )
with col_c2:
    child2 = st.selectbox(
        "Child 2",
        options=people,
        index=None,
        accept_new_options=True,
        placeholder="Select or type",
        key="am_child2",
    )

# ── SAVE ───────────────────────────────────────────────────────────────────
st.divider()

if st.button("Save", type="primary", use_container_width=True, key="am_save"):
    clean_name = (name or "").strip()
    clean_pubmed = (pubmed or "").strip()
    parents = [p for p in [parent1, parent2] if (p or "").strip()]
    children = [c for c in [child1, child2] if (c or "").strip()]

    if not selected_title.strip():
        set_status("Choose or name a tree before saving.", "error")
        st.rerun()

    if not clean_name:
        set_status("Enter a name before saving.", "error")
        st.rerun()

    box = get_or_create_box(dataset, selected_title.strip())

    # Find or create the person node; attach PubMed if provided.
    name_id = get_or_create_node(box, clean_name)
    if clean_pubmed:
        for node in box["nodes"]:
            if node["id"] == name_id:
                node["pubmed"] = clean_pubmed
                break

    added_links = 0
    warnings: list[str] = []

    for p_name in parents:
        p_clean = p_name.strip()
        p_id = get_or_create_node(box, p_clean)
        if p_id == name_id:
            warnings.append(f'"{p_clean}" cannot be their own parent.')
        elif add_link(box, p_id, name_id):
            added_links += 1
        else:
            warnings.append(f'"{p_clean}" → "{clean_name}" already linked.')

    for c_name in children:
        c_clean = c_name.strip()
        c_id = get_or_create_node(box, c_clean)
        if c_id == name_id:
            warnings.append(f'"{c_clean}" cannot be their own child.')
        elif add_link(box, name_id, c_id):
            added_links += 1
        else:
            warnings.append(f'"{clean_name}" → "{c_clean}" already linked.')

    persist_working_dataset()
    st.session_state.current_box_id = box["id"]

    parts = [f'Saved "{clean_name}" in "{box["title"]}"']
    if clean_pubmed:
        parts.append("with PubMed link")
    if added_links:
        parts.append(
            f"and {added_links} relationship{'s' if added_links != 1 else ''}"
        )
    parts.append("\u2014 awaiting admin approval.")
    msg = " ".join(parts)
    if warnings:
        msg += " Notes: " + " ".join(warnings)
    set_status(msg, "warning" if warnings else "success")
    st.rerun()

render_status_banner()
render_site_footer()
