"""Shared Streamlit UI: session state, Apple-style theme, and status helpers."""

from __future__ import annotations

import json

import streamlit as st

from retina_tree.data_utils import (
    get_current_box,
    serialize_dataset,
    slugify_id,
    unique_node_id,
)
from retina_tree.dataset_store import (
    has_pending_changes,
    load_working_dataset,
    save_working_dataset,
)
from retina_tree.search import PersonMatch, search_dataset
from retina_tree.branding import (
    LOGO_PATH,
    render_ambient_decor,
    render_brand_row,
    render_section_rule,
    site_footer_html,
)
from retina_tree.theme import APPLE_CSS


def inject_apple_theme() -> None:
    st.markdown(APPLE_CSS, unsafe_allow_html=True)
    st.markdown(render_ambient_decor(), unsafe_allow_html=True)


def configure_page(*, title: str, icon: str | None = None) -> None:
    page_icon = icon if icon is not None else str(LOGO_PATH)
    st.set_page_config(
        page_title=title,
        page_icon=page_icon,
        layout="wide",
        initial_sidebar_state="collapsed",
    )


def render_site_footer() -> None:
    st.markdown(site_footer_html(), unsafe_allow_html=True)


def init_session_state() -> None:
    defaults = {
        "dataset": None,
        "current_box_id": None,
        "view_mode": "roots-only",
        "status_message": "Loading data…",
        "status_type": "info",
        "search_query": "",
        "search_focus_key": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def ensure_dataset_loaded() -> None:
    init_session_state()
    if st.session_state.dataset is None:
        reload_working_dataset()


def set_status(message: str, status_type: str = "info") -> None:
    st.session_state.status_message = message
    st.session_state.status_type = status_type


def reload_working_dataset() -> None:
    try:
        dataset = load_working_dataset()
        st.session_state.dataset = dataset
        st.session_state.current_box_id = dataset["boxes"][0]["id"] if dataset["boxes"] else None
        pending = has_pending_changes()
        box_count = len(dataset["boxes"])
        if pending:
            set_status(
                f"Showing {box_count} tree{'s' if box_count != 1 else ''} "
                "(includes unpublished edits awaiting admin review).",
                "warning",
            )
        else:
            set_status(f"Showing {box_count} tree{'s' if box_count != 1 else ''}.", "success")
    except FileNotFoundError:
        set_status("Working dataset file not found.", "error")
    except json.JSONDecodeError as exc:
        set_status(f"Invalid working JSON: {exc}", "error")
    except OSError as exc:
        set_status(f"Could not load working dataset: {exc}", "error")


def persist_working_dataset() -> None:
    save_working_dataset(st.session_state.dataset)


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
        f'<div class="rt-hero-shell">{render_brand_row(title=title, subtitle=subtitle, show_tagline=False)}</div>',
        unsafe_allow_html=True,
    )


def render_home_header() -> None:
    """Logo + dataset title + nav links for the home page."""
    dataset = st.session_state.dataset
    title = dataset["title"] if dataset else "Retina Trees"
    st.markdown(
        f'<div class="rt-hero-shell">{render_brand_row(title=title, show_tagline=True)}</div>',
        unsafe_allow_html=True,
    )


def render_pending_badge() -> None:
    if has_pending_changes():
        st.markdown(
            '<span class="apple-pill warn">Unpublished edits · admin review pending</span>',
            unsafe_allow_html=True,
        )


def render_view_toolbar() -> None:
    col_label, col_mode, col_edit = st.columns([1.2, 2.2, 1.2])

    with col_label:
        pill = (
            '<span class="apple-pill warn">Live + pending</span>'
            if has_pending_changes()
            else '<span class="apple-pill">Live</span>'
        )
        st.markdown(
            f'<div class="apple-toolbar"><span class="label">View</span>{pill}</div>',
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


def _match_option_label(match: PersonMatch) -> str:
    pct = int(round(match.score * 100))
    return f"{match.label} ({match.node_id}) · {match.box_title} · {pct}%"


def render_person_search() -> tuple[str | None, str | None, set[str]]:
    """
    Search UI. Returns (filter_box_id, focus_node_id, highlight_node_ids) for the active box.
    """
    dataset = st.session_state.dataset
    if not dataset:
        return None, None, set()

    st.markdown(render_section_rule(label="Search"), unsafe_allow_html=True)

    query = st.text_input(
        "Search",
        value=st.session_state.search_query,
        placeholder="Name or ID — fuzzy match (e.g. Dowling, Wald, JED)",
        label_visibility="collapsed",
        key="person_search_input",
    )
    st.session_state.search_query = query

    if not query.strip():
        st.session_state.search_focus_key = None
        return None, None, set()

    matches = search_dataset(dataset, query)
    if not matches:
        st.caption("No matches. Try a shorter spelling or part of a name.")
        return None, None, set()

    options = [f"{m.box_id}|{m.node_id}" for m in matches]
    labels = {opt: _match_option_label(m) for opt, m in zip(options, matches)}

    if st.session_state.search_focus_key not in options:
        st.session_state.search_focus_key = options[0]

    selected_key = st.selectbox(
        "Matches",
        options=options,
        index=options.index(st.session_state.search_focus_key),
        format_func=lambda k: labels[k],
        label_visibility="collapsed",
    )
    st.session_state.search_focus_key = selected_key

    match = next(m for m in matches if f"{m.box_id}|{m.node_id}" == selected_key)
    highlight_ids = {m.node_id for m in matches if m.box_id == match.box_id}

    st.caption(
        f"Showing **{match.label}** in *{match.box_title}* "
        f"({len(matches)} fuzzy match{'es' if len(matches) != 1 else ''})."
    )
    return match.box_id, match.node_id, highlight_ids


def render_box_filter(*, search_box_id: str | None = None) -> str | None:
    dataset = st.session_state.dataset
    if not dataset or not dataset.get("boxes"):
        return None

    if search_box_id:
        return search_box_id

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
        st.page_link("pages/Admin_Review.py", label="Admin review", icon="🛡️", use_container_width=True)

    st.info(
        "Changes apply **immediately** on the home page. The **original** dataset is unchanged until "
        "an administrator accepts them. Rejecting reverts the live view to the last permanent version."
    )
    render_pending_badge()

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

    st.markdown(render_section_rule(label="Edit"), unsafe_allow_html=True)
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
                persist_working_dataset()
                set_status(f"Added node {node_id}. Visible on trees now; awaiting admin to make permanent.", "success")
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
                if st.button("Save label", use_container_width=True, key="save_label"):
                    cleaned = new_label.strip()
                    if not cleaned:
                        set_status("Label cannot be empty.", "error")
                    else:
                        active_node["label"] = cleaned
                        persist_working_dataset()
                        set_status("Label updated on live trees.", "success")
                        st.rerun()
            with b2:
                if st.button("Delete", use_container_width=True, type="secondary", key="del_node"):
                    box["nodes"] = [n for n in box["nodes"] if n["id"] != selected_node_id]
                    box["links"] = [
                        link
                        for link in box["links"]
                        if link["parent"] != selected_node_id and link["child"] != selected_node_id
                    ]
                    persist_working_dataset()
                    set_status("Node removed from live trees.", "success")
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
                    persist_working_dataset()
                    set_status("Link added on live trees.", "success")
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
                    persist_working_dataset()
                    set_status("Link removed from live trees.", "success")
                    st.rerun()

    render_status_banner()

    with st.expander("Live JSON (working copy)"):
        st.code(serialize_dataset(dataset), language="json")
