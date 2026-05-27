"""Shared Streamlit UI: session state, Apple-style theme, and status helpers."""

from __future__ import annotations

import json

import streamlit as st

from retina_tree.data_utils import (
    DEFAULT_JSON_PATH,
    get_current_box,
    load_dataset_from_path,
    load_dataset_from_text,
    serialize_dataset,
    slugify_id,
    unique_node_id,
)
from retina_tree.theme import APPLE_CSS


def inject_apple_theme() -> None:
    st.markdown(APPLE_CSS, unsafe_allow_html=True)


def configure_page(*, title: str, icon: str = "🌳") -> None:
    st.set_page_config(
        page_title=title,
        page_icon=icon,
        layout="wide",
        initial_sidebar_state="collapsed",
    )


def init_session_state() -> None:
    defaults = {
        "dataset": None,
        "current_box_id": None,
        "source_name": str(DEFAULT_JSON_PATH.name),
        "dirty": False,
        "view_mode": "roots-only",
        "status_message": "Loading data…",
        "status_type": "info",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def ensure_dataset_loaded() -> None:
    init_session_state()
    if st.session_state.dataset is None:
        load_default_dataset()


def set_status(message: str, status_type: str = "info") -> None:
    st.session_state.status_message = message
    st.session_state.status_type = status_type


def load_default_dataset() -> None:
    try:
        dataset = load_dataset_from_path(DEFAULT_JSON_PATH)
        st.session_state.dataset = dataset
        st.session_state.current_box_id = dataset["boxes"][0]["id"] if dataset["boxes"] else None
        st.session_state.source_name = DEFAULT_JSON_PATH.name
        st.session_state.dirty = False
        box_count = len(dataset["boxes"])
        set_status(
            f"Loaded {box_count} tree{'s' if box_count != 1 else ''} from {DEFAULT_JSON_PATH.name}.",
            "success",
        )
    except FileNotFoundError:
        set_status(f"Default JSON not found at {DEFAULT_JSON_PATH}.", "error")
    except json.JSONDecodeError as exc:
        set_status(f"Invalid JSON in default file: {exc}", "error")
    except OSError as exc:
        set_status(f"Could not read default JSON: {exc}", "error")


def mark_dirty(message: str) -> None:
    st.session_state.dirty = True
    set_status(message, "warning")


def render_status_banner() -> None:
    suffix = " · Unsaved changes" if st.session_state.dirty else ""
    message = f"{st.session_state.status_message}{suffix}"
    css_class = st.session_state.status_type
    if css_class == "info":
        css_class = "success"
    st.markdown(
        f'<div class="status-banner {css_class}">{message}</div>',
        unsafe_allow_html=True,
    )


def render_page_header(*, subtitle: str) -> None:
    dataset = st.session_state.dataset
    title = dataset["title"] if dataset else "Retina Trees"
    st.markdown(
        f"""
        <div class="apple-hero">
          <h1>{title}</h1>
          <p class="subtitle">{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_view_toolbar() -> None:
    """Segmented view controls for the home page."""
    col_label, col_mode, col_edit = st.columns([1.2, 2.2, 1.2])

    with col_label:
        dirty_pill = (
            '<span class="apple-pill warn">Unsaved</span>'
            if st.session_state.dirty
            else f'<span class="apple-pill">{st.session_state.source_name}</span>'
        )
        st.markdown(
            f'<div class="apple-toolbar"><span class="label">Source</span>{dirty_pill}</div>',
            unsafe_allow_html=True,
        )

    with col_mode:
        mode_labels = ["Roots only", "Expand all", "Collapse all"]
        mode_keys = ["roots-only", "expand-all", "collapse-all"]
        current_index = mode_keys.index(st.session_state.view_mode) if st.session_state.view_mode in mode_keys else 0
        mode = st.radio(
            "View",
            options=mode_labels,
            index=current_index,
            horizontal=True,
            label_visibility="collapsed",
        )
        mapping = dict(zip(mode_labels, mode_keys))
        new_mode = mapping[mode]
        if new_mode != st.session_state.view_mode:
            st.session_state.view_mode = new_mode
            st.rerun()

    with col_edit:
        st.page_link("pages/Edit_Data.py", label="Edit data", icon="✏️", use_container_width=True)


def render_box_filter() -> str | None:
    dataset = st.session_state.dataset
    if not dataset or not dataset.get("boxes"):
        return None

    options = ["All trees", *[
        f"{box['title']} ({len(box['nodes'])} nodes)" for box in dataset["boxes"]
    ]]
    box_ids = [None, *[box["id"] for box in dataset["boxes"]]]

    selected = st.selectbox(
        "Focus",
        options=range(len(options)),
        format_func=lambda i: options[i],
        label_visibility="collapsed",
    )
    return box_ids[selected]


def render_editor_page() -> None:
    dataset = st.session_state.dataset
    if not dataset or not dataset.get("boxes"):
        st.info("No data loaded. Return to the viewer or reload the default JSON.")
        return

    boxes = dataset["boxes"]
    box = get_current_box(dataset, st.session_state.current_box_id)
    if box is None:
        return

    st.session_state.current_box_id = box["id"]

    top_left, top_right = st.columns([3, 1])
    with top_left:
        st.page_link("app.py", label="← Back to trees", icon="🌳")
    with top_right:
        st.download_button(
            "Download JSON",
            data=serialize_dataset(dataset),
            file_name="retina_trees_data.json",
            mime="application/json",
            use_container_width=True,
        )

    st.markdown('<p class="apple-section-label">Dataset</p>', unsafe_allow_html=True)
    with st.container():
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("Reload default", use_container_width=True, type="secondary"):
                load_default_dataset()
                st.rerun()
        with c2:
            if st.button(
                "Discard edits",
                use_container_width=True,
                type="secondary",
                disabled=not st.session_state.dirty,
            ):
                load_default_dataset()
                st.rerun()
        with c3:
            uploaded = st.file_uploader(
                "Upload JSON",
                type=["json"],
                label_visibility="collapsed",
            )
        if uploaded is not None:
            try:
                text = uploaded.getvalue().decode("utf-8")
                new_dataset = load_dataset_from_text(text)
                st.session_state.dataset = new_dataset
                st.session_state.current_box_id = (
                    new_dataset["boxes"][0]["id"] if new_dataset["boxes"] else None
                )
                st.session_state.source_name = uploaded.name
                st.session_state.dirty = False
                set_status(f"Loaded {len(new_dataset['boxes'])} trees from {uploaded.name}.", "success")
                st.rerun()
            except json.JSONDecodeError as exc:
                set_status(f"Invalid JSON file: {exc}", "error")

    render_status_banner()

    box_labels = {item["id"]: item["title"] for item in boxes}
    selected_box_id = st.selectbox(
        "Tree box",
        options=list(box_labels.keys()),
        format_func=lambda box_id: box_labels[box_id],
        index=list(box_labels.keys()).index(box["id"]),
    )
    if selected_box_id != st.session_state.current_box_id:
        st.session_state.current_box_id = selected_box_id
        st.rerun()

    box = get_current_box(dataset, st.session_state.current_box_id)
    if box is None:
        return

    st.caption(f"{len(box['nodes'])} nodes · {len(box['links'])} links")

    st.markdown('<p class="apple-section-label">Nodes & links</p>', unsafe_allow_html=True)
    left, mid, right = st.columns(3)

    with left:
        st.markdown("### Add node")
        add_node_id = st.text_input("Node ID", placeholder="Auto from label if empty", key="add_id")
        add_node_label = st.text_input("Label", placeholder="Display name", key="add_label")
        if st.button("Add node", use_container_width=True, key="add_btn"):
            label = add_node_label.strip()
            if not label:
                set_status("Enter a node label before adding.", "error")
            else:
                requested_id = add_node_id.strip() or slugify_id(label)
                node_id = unique_node_id(box, requested_id)
                box["nodes"].append({"id": node_id, "label": label})
                mark_dirty(f"Added node {node_id}.")
                st.rerun()

    with mid:
        st.markdown("### Edit node")
        if not box["nodes"]:
            st.caption("No nodes in this box.")
        else:
            node_options = {n["id"]: f"{n['label']} ({n['id']})" for n in box["nodes"]}
            selected_node_id = st.selectbox(
                "Node",
                options=list(node_options.keys()),
                format_func=lambda nid: node_options[nid],
                key="edit_node_sel",
            )
            active_node = next(n for n in box["nodes"] if n["id"] == selected_node_id)
            new_label = st.text_input("Label", value=active_node["label"], key="edit_label")
            b1, b2 = st.columns(2)
            with b1:
                if st.button("Save", use_container_width=True, key="save_label"):
                    cleaned = new_label.strip()
                    if not cleaned:
                        set_status("Label cannot be empty.", "error")
                    else:
                        active_node["label"] = cleaned
                        mark_dirty(f"Updated {active_node['id']}.")
                        st.rerun()
            with b2:
                if st.button("Delete", use_container_width=True, type="secondary", key="del_node"):
                    box["nodes"] = [n for n in box["nodes"] if n["id"] != selected_node_id]
                    box["links"] = [
                        link
                        for link in box["links"]
                        if link["parent"] != selected_node_id and link["child"] != selected_node_id
                    ]
                    mark_dirty(f"Deleted {selected_node_id}.")
                    st.rerun()

    with right:
        st.markdown("### Links")
        if len(box["nodes"]) < 2:
            st.caption("Need at least two nodes.")
        else:
            node_options = {n["id"]: f"{n['label']} ({n['id']})" for n in box["nodes"]}
            parent_id = st.selectbox(
                "Parent",
                options=list(node_options.keys()),
                format_func=lambda nid: node_options[nid],
                key="link_parent",
            )
            child_id = st.selectbox(
                "Child",
                options=list(node_options.keys()),
                format_func=lambda nid: node_options[nid],
                key="link_child",
            )
            if st.button("Add link", use_container_width=True, key="add_link"):
                if parent_id == child_id:
                    set_status("Parent and child must differ.", "error")
                elif any(
                    link["parent"] == parent_id and link["child"] == child_id for link in box["links"]
                ):
                    set_status("Link already exists.", "error")
                else:
                    box["links"].append({"parent": parent_id, "child": child_id})
                    mark_dirty("Added link.")
                    st.rerun()

            link_labels = {
                f"{link['parent']}->{link['child']}": (
                    f"{node_options.get(link['parent'], link['parent'])} → "
                    f"{node_options.get(link['child'], link['child'])}"
                )
                for link in box["links"]
            }
            if link_labels:
                selected_link = st.selectbox("Existing", options=list(link_labels.keys()), key="link_sel")
                if st.button("Delete link", use_container_width=True, type="secondary", key="del_link"):
                    parent, child = selected_link.split("->", 1)
                    box["links"] = [
                        link
                        for link in box["links"]
                        if not (link["parent"] == parent and link["child"] == child)
                    ]
                    mark_dirty("Deleted link.")
                    st.rerun()

    st.markdown('<p class="apple-section-label">JSON preview</p>', unsafe_allow_html=True)
    st.code(serialize_dataset(dataset), language="json")
