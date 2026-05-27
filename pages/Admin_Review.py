"""Compare original vs live data; accept (permanent) or reject (revert)."""

from __future__ import annotations

import site_setup  # noqa: F401

import streamlit as st

from rtree.admin_access import render_admin_access_gate
from rtree.dataset_diff import diff_datasets, summarize_changes
from rtree.dataset_store import (
    accept_all_changes,
    has_pending_changes,
    load_original_dataset,
    load_working_dataset,
    reject_all_changes,
)
from rtree.ui import (
    configure_page,
    ensure_dataset_loaded,
    inject_apple_theme,
    reload_working_dataset,
    render_page_header,
    render_site_footer,
    render_status_banner,
    set_status,
)

configure_page(title="Admin Review · Retina Trees")
inject_apple_theme()
render_admin_access_gate()
ensure_dataset_loaded()

render_page_header(
    subtitle="Review differences between the permanent original and the live working copy. "
    "Accept saves changes permanently; reject restores the live view to the original."
)

st.page_link("app.py", label="← Back to trees", icon="🌳")

original = load_original_dataset()
working = load_working_dataset()

if not has_pending_changes():
    st.success("Live data matches the permanent original. Nothing to review.")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Original nodes", sum(len(b["nodes"]) for b in original.get("boxes", [])))
    with col2:
        st.metric("Live nodes", sum(len(b["nodes"]) for b in working.get("boxes", [])))
    st.stop()

changes = diff_datasets(original, working)
summary = summarize_changes(original, working)

st.warning(f"{len(changes)} unpublished change{'s' if len(changes) != 1 else ''} on the live trees.")

metric_cols = st.columns(min(len(summary) or 1, 4))
for idx, (label, count) in enumerate(summary.items()):
    with metric_cols[idx % len(metric_cols)]:
        st.metric(label, count)

st.markdown('<p class="apple-section-label">Change log</p>', unsafe_allow_html=True)
st.dataframe(changes, use_container_width=True, hide_index=True)

st.markdown('<p class="apple-section-label">Side-by-side JSON</p>', unsafe_allow_html=True)
left, right = st.columns(2)
with left:
    st.markdown("**Original (permanent)**")
    st.json(original)
with right:
    st.markdown("**Live (working)**")
    st.json(working)

st.markdown('<p class="apple-section-label">Decision</p>', unsafe_allow_html=True)
accept_col, reject_col, _ = st.columns([1, 1, 2])

with accept_col:
    if st.button("Accept all changes", type="primary", use_container_width=True):
        accept_all_changes()
        reload_working_dataset()
        set_status("All changes are now permanent. Original and live data match.", "success")
        st.rerun()

with reject_col:
    if st.button("Reject all (revert live)", type="secondary", use_container_width=True):
        reject_all_changes()
        reload_working_dataset()
        set_status("Live data reverted to the permanent original.", "success")
        st.rerun()

render_status_banner()
render_site_footer()
