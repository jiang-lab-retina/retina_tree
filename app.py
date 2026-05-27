"""Streamlit retina tree viewer — auto-loads bundled JSON and renders linkage trees."""

from __future__ import annotations

import json

import streamlit as st
import streamlit.components.v1 as components

from retina_tree.data_utils import (
    DEFAULT_JSON_PATH,
    get_current_box,
    load_dataset_from_path,
    load_dataset_from_text,
    serialize_dataset,
    slugify_id,
    unique_node_id,
)
from retina_tree.tree_html import estimate_card_height, render_tree_card_html

APP_CSS = """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:wght@600;700&display=swap');

  .stApp {
    background:
      radial-gradient(circle at top left, rgba(23, 95, 109, 0.08), transparent 24rem),
      linear-gradient(180deg, #f8f4ec 0%, #f1e9dc 100%);
    color: #1f2833;
  }

  .block-container {
    max-width: 1440px;
    padding-top: 1.5rem;
    padding-bottom: 3rem;
  }

  .hero-card {
    background: rgba(255, 250, 241, 0.92);
    border: 1px solid rgba(23, 95, 109, 0.14);
    border-radius: 22px;
    box-shadow: 0 16px 42px rgba(23, 44, 53, 0.12);
    padding: 1.4rem 1.4rem 1rem;
    margin-bottom: 1rem;
  }

  .hero-card h1 {
    font-family: Georgia, "Times New Roman", serif;
    letter-spacing: -0.02em;
    margin: 0 0 0.35rem;
    font-size: clamp(2rem, 3vw, 2.6rem);
  }

  .hero-card p {
    color: #5d6874;
    margin: 0.2rem 0;
  }

  .status-success {
    background: #dff3e8;
    color: #216047;
    border: 1px solid rgba(33, 96, 71, 0.2);
    border-radius: 14px;
    padding: 0.7rem 0.9rem;
    margin-top: 0.8rem;
  }

  .status-warning {
    background: #fff1cc;
    color: #8d5b15;
    border: 1px solid rgba(141, 91, 21, 0.2);
    border-radius: 14px;
    padding: 0.7rem 0.9rem;
    margin-top: 0.8rem;
  }

  .status-error {
    background: #fde2df;
    color: #8b2f2b;
    border: 1px solid rgba(139, 47, 43, 0.2);
    border-radius: 14px;
    padding: 0.7rem 0.9rem;
    margin-top: 0.8rem;
  }

  div[data-testid="stExpander"] {
    background: rgba(255, 250, 241, 0.9);
    border: 1px solid rgba(23, 95, 109, 0.14);
    border-radius: 18px;
  }
</style>
"""


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
            f"Loaded {box_count} box{'es' if box_count != 1 else ''} from {DEFAULT_JSON_PATH.name}.",
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


def render_status() -> None:
    suffix = " Unsaved changes." if st.session_state.dirty else ""
    message = f"{st.session_state.status_message}{suffix}"
    css_class = {
        "success": "status-success",
        "warning": "status-warning",
        "error": "status-error",
    }.get(st.session_state.status_type, "status-success")
    st.markdown(f'<div class="{css_class}">{message}</div>', unsafe_allow_html=True)


def render_hero() -> None:
    dataset = st.session_state.dataset
    title = dataset["title"] if dataset else "Retina Trees Viewer"

    st.markdown(
        f"""
        <div class="hero-card">
          <h1>{title}</h1>
          <p>This app renders retina tree linkage data from <code>data/retina_trees_data.json</code>
          on startup. You can upload a different JSON file, edit nodes and links, and download updates.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        if st.button("Expand all", use_container_width=True):
            st.session_state.view_mode = "expand-all"
            st.rerun()
    with col2:
        if st.button("Collapse all", use_container_width=True):
            st.session_state.view_mode = "collapse-all"
            st.rerun()
    with col3:
        if st.button("Roots only", use_container_width=True):
            st.session_state.view_mode = "roots-only"
            st.rerun()
    with col4:
        if st.button("Reload default JSON", use_container_width=True):
            load_default_dataset()
            st.rerun()
    with col5:
        if st.button("Discard edits", use_container_width=True, disabled=not st.session_state.dirty):
            load_default_dataset()
            st.rerun()

    uploaded = st.file_uploader("Open JSON", type=["json"], label_visibility="collapsed")
    if uploaded is not None:
        try:
            text = uploaded.getvalue().decode("utf-8")
            dataset = load_dataset_from_text(text)
            st.session_state.dataset = dataset
            st.session_state.current_box_id = dataset["boxes"][0]["id"] if dataset["boxes"] else None
            st.session_state.source_name = uploaded.name
            st.session_state.dirty = False
            set_status(f"Loaded {len(dataset['boxes'])} boxes from {uploaded.name}.", "success")
            st.rerun()
        except json.JSONDecodeError as exc:
            set_status(f"Invalid JSON file: {exc}", "error")

    render_status()

    if dataset:
        st.download_button(
            "Download JSON",
            data=serialize_dataset(dataset),
            file_name="retina_trees_data.json",
            mime="application/json",
            use_container_width=False,
        )


def render_editor() -> None:
    dataset = st.session_state.dataset
    if not dataset or not dataset.get("boxes"):
        st.info("No boxes loaded. Upload a JSON file or reload the default dataset.")
        return

    boxes = dataset["boxes"]
    box = get_current_box(dataset, st.session_state.current_box_id)
    if box is None:
        return

    st.session_state.current_box_id = box["id"]

    with st.expander("Edit dataset", expanded=False):
        box_labels = {item["id"]: item["title"] for item in boxes}
        selected_box_id = st.selectbox(
            "Box",
            options=list(box_labels.keys()),
            format_func=lambda box_id: box_labels[box_id],
            index=list(box_labels.keys()).index(box["id"]),
            key="box_select",
        )
        if selected_box_id != st.session_state.current_box_id:
            st.session_state.current_box_id = selected_box_id
            st.rerun()

        box = get_current_box(dataset, st.session_state.current_box_id)
        if box is None:
            return

        st.caption(f"{len(box['nodes'])} nodes · {len(box['links'])} links in this box.")

        left, mid, right = st.columns(3)

        with left:
            st.subheader("Add node")
            add_node_id = st.text_input("Node ID", placeholder="Optional; generated from label if blank")
            add_node_label = st.text_input("Node label", placeholder="Display name")
            if st.button("Add node", use_container_width=True):
                label = add_node_label.strip()
                if not label:
                    set_status("Enter a node label before adding a node.", "error")
                else:
                    requested_id = add_node_id.strip() or slugify_id(label)
                    node_id = unique_node_id(box, requested_id)
                    box["nodes"].append({"id": node_id, "label": label})
                    mark_dirty(f"Added node {node_id}.")
                    st.rerun()

        with mid:
            st.subheader("Edit node")
            if not box["nodes"]:
                st.caption("No nodes in this box.")
            else:
                node_options = {node["id"]: f"{node['label']} ({node['id']})" for node in box["nodes"]}
                selected_node_id = st.selectbox(
                    "Node",
                    options=list(node_options.keys()),
                    format_func=lambda node_id: node_options[node_id],
                )
                active_node = next(node for node in box["nodes"] if node["id"] == selected_node_id)
                new_label = st.text_input("Label", value=active_node["label"])
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("Update label", use_container_width=True):
                        cleaned = new_label.strip()
                        if not cleaned:
                            set_status("Node label cannot be empty.", "error")
                        else:
                            active_node["label"] = cleaned
                            mark_dirty(f"Updated label for {active_node['id']}.")
                            st.rerun()
                with c2:
                    if st.button("Delete node", use_container_width=True, type="primary"):
                        box["nodes"] = [node for node in box["nodes"] if node["id"] != selected_node_id]
                        box["links"] = [
                            link
                            for link in box["links"]
                            if link["parent"] != selected_node_id and link["child"] != selected_node_id
                        ]
                        mark_dirty(f"Deleted node {selected_node_id}.")
                        st.rerun()

        with right:
            st.subheader("Links")
            if len(box["nodes"]) < 2:
                st.caption("Add at least two nodes to create links.")
            else:
                node_options = {node["id"]: f"{node['label']} ({node['id']})" for node in box["nodes"]}
                parent_id = st.selectbox(
                    "Parent",
                    options=list(node_options.keys()),
                    format_func=lambda node_id: node_options[node_id],
                    key="link_parent",
                )
                child_id = st.selectbox(
                    "Child",
                    options=list(node_options.keys()),
                    format_func=lambda node_id: node_options[node_id],
                    key="link_child",
                )
                if st.button("Add link", use_container_width=True):
                    if parent_id == child_id:
                        set_status("Parent and child must be different.", "error")
                    elif any(
                        link["parent"] == parent_id and link["child"] == child_id for link in box["links"]
                    ):
                        set_status("That link already exists.", "error")
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
                    selected_link = st.selectbox("Existing links", options=list(link_labels.keys()))
                    if st.button("Delete selected link", use_container_width=True):
                        parent, child = selected_link.split("->", 1)
                        box["links"] = [
                            link
                            for link in box["links"]
                            if not (link["parent"] == parent and link["child"] == child)
                        ]
                        mark_dirty("Deleted link.")
                        st.rerun()

        st.subheader("JSON preview")
        st.code(serialize_dataset(dataset), language="json")


def render_trees() -> None:
    dataset = st.session_state.dataset
    if not dataset or not dataset.get("boxes"):
        st.warning("No boxes loaded.")
        return

    st.subheader("Trees")
    view_mode = st.session_state.view_mode
    current_box_id = st.session_state.current_box_id

    for box in dataset["boxes"]:
        card_html = render_tree_card_html(
            box,
            current_box_id=current_box_id,
            view_mode=view_mode,
            card_id=box["id"],
        )
        height = estimate_card_height(box)
        components.html(card_html, height=height, scrolling=True)


def main() -> None:
    st.set_page_config(
        page_title="Retina Trees Viewer",
        page_icon="🌳",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    init_session_state()
    st.markdown(APP_CSS, unsafe_allow_html=True)

    if st.session_state.dataset is None:
        load_default_dataset()

    render_hero()
    render_editor()
    render_trees()


if __name__ == "__main__":
    main()
