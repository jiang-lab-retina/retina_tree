"""Shared Streamlit UI: session state, Apple-style theme, and status helpers."""

from __future__ import annotations

import json

import streamlit as st

from retina_tree.auth import (
    current_user_email,
    is_admin,
    render_account_bar,
    render_login_gate,
    submit_edit_proposal,
)
from retina_tree.data_utils import (
    get_current_box,
    serialize_dataset,
    slugify_id,
)
from retina_tree.dataset_store import load_approved_dataset
from retina_tree.proposal_apply import build_summary
from retina_tree.proposals_db import list_proposals
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
        "source_name": "approved_dataset.json",
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
        reload_approved_dataset()


def set_status(message: str, status_type: str = "info") -> None:
    st.session_state.status_message = message
    st.session_state.status_type = status_type


def reload_approved_dataset() -> None:
    try:
        dataset = load_approved_dataset()
        st.session_state.dataset = dataset
        st.session_state.current_box_id = dataset["boxes"][0]["id"] if dataset["boxes"] else None
        st.session_state.source_name = "approved_dataset.json"
        box_count = len(dataset["boxes"])
        set_status(
            f"Showing {box_count} approved tree{'s' if box_count != 1 else ''}.",
            "success",
        )
    except FileNotFoundError:
        set_status("Approved dataset file not found.", "error")
    except json.JSONDecodeError as exc:
        set_status(f"Invalid approved JSON: {exc}", "error")
    except OSError as exc:
        set_status(f"Could not load approved dataset: {exc}", "error")


def render_status_banner() -> None:
    message = st.session_state.status_message
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
    col_label, col_mode, col_edit = st.columns([1.2, 2.2, 1.2])

    with col_label:
        st.markdown(
            f'<div class="apple-toolbar"><span class="label">Dataset</span>'
            f'<span class="apple-pill">Approved</span></div>',
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
        st.page_link("pages/Edit_Data.py", label="Propose edit", icon="✏️", use_container_width=True)


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


def _submit_and_notify(action: str, box: dict, payload: dict) -> None:
    summary = build_summary(action, payload, box["title"])
    try:
        proposal_id = submit_edit_proposal(
            action=action,
            box_id=box["id"],
            box_title=box["title"],
            payload=payload,
            summary=summary,
        )
        set_status(
            f"Submitted for review (id {proposal_id[:8]}…). An administrator will approve or reject it.",
            "success",
        )
    except Exception as exc:
        set_status(f"Could not submit proposal: {exc}", "error")


def render_user_proposals_table() -> None:
    email = current_user_email()
    if not email:
        return

    proposals = list_proposals(user_email=email, limit=50)
    if not proposals:
        st.caption("You have not submitted any edits yet.")
        return

    st.markdown('<p class="apple-section-label">Your submissions</p>', unsafe_allow_html=True)
    rows = []
    for p in proposals:
        rows.append(
            {
                "When": p["created_at"][:19].replace("T", " "),
                "Status": p["status"],
                "Change": p["summary"],
                "Review note": p.get("review_note") or "—",
            }
        )
    st.dataframe(rows, use_container_width=True, hide_index=True)


def render_editor_page() -> None:
    render_login_gate(
        message="Sign in with Google to propose changes. Edits are tracked and require administrator approval before they appear on the public trees."
    )

    dataset = st.session_state.dataset
    if not dataset or not dataset.get("boxes"):
        st.info("No data loaded.")
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
        if is_admin():
            st.page_link("pages/Admin_Review.py", label="Admin review", icon="🛡️", use_container_width=True)

    st.info(
        "The trees on the home page show **approved** data only. Your changes below are saved as "
        "**proposals** and will not appear publicly until an administrator approves them."
    )

    render_account_bar()

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

    st.caption(f"{len(box['nodes'])} nodes · {len(box['links'])} links (approved snapshot)")

    st.markdown('<p class="apple-section-label">Propose changes</p>', unsafe_allow_html=True)
    left, mid, right = st.columns(3)

    with left:
        st.markdown("### Add node")
        add_node_id = st.text_input("Node ID", placeholder="Auto from label if empty", key="add_id")
        add_node_label = st.text_input("Label", placeholder="Display name", key="add_label")
        if st.button("Submit add node", use_container_width=True, key="add_btn"):
            label = add_node_label.strip()
            if not label:
                set_status("Enter a node label before submitting.", "error")
            else:
                payload = {
                    "label": label,
                    "node_id": add_node_id.strip() or slugify_id(label),
                }
                _submit_and_notify("add_node", box, payload)
                st.rerun()

    with mid:
        st.markdown("### Edit node label")
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
            new_label = st.text_input("New label", value=active_node["label"], key="edit_label")
            if st.button("Submit label change", use_container_width=True, key="save_label"):
                cleaned = new_label.strip()
                if not cleaned:
                    set_status("Label cannot be empty.", "error")
                elif cleaned == active_node["label"]:
                    set_status("Label is unchanged.", "warning")
                else:
                    payload = {"node_id": selected_node_id, "label": cleaned}
                    _submit_and_notify("update_node", box, payload)
                    st.rerun()

            if st.button("Submit delete node", use_container_width=True, type="secondary", key="del_node"):
                payload = {"node_id": selected_node_id}
                _submit_and_notify("delete_node", box, payload)
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
            if st.button("Submit add link", use_container_width=True, key="add_link"):
                if parent_id == child_id:
                    set_status("Parent and child must differ.", "error")
                elif any(
                    link["parent"] == parent_id and link["child"] == child_id for link in box["links"]
                ):
                    set_status("Link already exists in approved data.", "error")
                else:
                    payload = {"parent": parent_id, "child": child_id}
                    _submit_and_notify("add_link", box, payload)
                    st.rerun()

            link_labels = {
                f"{link['parent']}->{link['child']}": (
                    f"{node_options.get(link['parent'], link['parent'])} → "
                    f"{node_options.get(link['child'], link['child'])}"
                )
                for link in box["links"]
            }
            if link_labels:
                selected_link = st.selectbox("Existing link", options=list(link_labels.keys()), key="link_sel")
                if st.button("Submit delete link", use_container_width=True, type="secondary", key="del_link"):
                    parent, child = selected_link.split("->", 1)
                    payload = {"parent": parent, "child": child}
                    _submit_and_notify("delete_link", box, payload)
                    st.rerun()

    render_status_banner()
    render_user_proposals_table()

    with st.expander("Approved JSON snapshot (read-only)"):
        st.code(serialize_dataset(dataset), language="json")
