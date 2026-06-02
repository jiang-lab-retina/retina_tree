"""Compare original vs live data; accept (permanent) or reject (revert)."""

from __future__ import annotations

import site_setup  # noqa: F401

import streamlit as st

from rtree.admin_access import render_admin_access_gate
from rtree.dataset_diff import diff_datasets, summarize_changes
from rtree.dataset_store import (
    accept_all_changes,
    accept_single_change,
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

configure_page(title="Admin Review · Retina Tree")
inject_apple_theme()
render_admin_access_gate()
ensure_dataset_loaded()

render_page_header(
    subtitle="Review each pending change. Accept individually or all at once. "
    "Reject all reverts the live view to the last permanent version."
)

st.page_link("app.py", label="← Back to trees", icon="🌳")

original = load_original_dataset()
working  = load_working_dataset()

if not has_pending_changes():
    st.success("Live data matches the permanent original. Nothing to review.")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Original nodes", sum(len(b["nodes"]) for b in original.get("boxes", [])))
    with col2:
        st.metric("Live nodes", sum(len(b["nodes"]) for b in working.get("boxes", [])))
    render_site_footer()
    st.stop()

changes = diff_datasets(original, working)
summary = summarize_changes(original, working)

st.warning(f"{len(changes)} unpublished change{'s' if len(changes) != 1 else ''} on the live trees.")

metric_cols = st.columns(min(len(summary) or 1, 4))
for idx, (label, count) in enumerate(summary.items()):
    with metric_cols[idx % len(metric_cols)]:
        st.metric(label, count)

# ── Accept all / Reject all ──────────────────────────────────────────────────
st.markdown("---")
bulk_accept, bulk_reject, _ = st.columns([1, 1, 2])
with bulk_accept:
    if st.button("Accept all changes", type="primary", use_container_width=True, key="accept_all"):
        accept_all_changes()
        reload_working_dataset()
        set_status("All changes are now permanent.", "success")
        st.rerun()
with bulk_reject:
    if st.button("Reject all (revert live)", type="secondary", use_container_width=True, key="reject_all"):
        reject_all_changes()
        reload_working_dataset()
        set_status("Live data reverted to the permanent original.", "success")
        st.rerun()

# ── Per-change review ────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### Changes")
st.caption("Click **Accept** on a single row to make just that change permanent.")

# Group by box for readability
box_order: list[str] = []
by_box: dict[str, list[dict]] = {}
for ch in changes:
    bid = ch["box_id"]
    if bid not in by_box:
        box_order.append(bid)
        by_box[bid] = []
    by_box[bid].append(ch)

TYPE_ICONS = {
    "Box renamed":  "🏷️",
    "Node added":   "➕",
    "Node renamed": "✏️",
    "Node removed": "🗑️",
    "Link added":   "🔗",
    "Link removed": "✂️",
}

for box_id in box_order:
    box_changes = by_box[box_id]
    box_label   = box_changes[0]["box"]
    st.markdown(f"**Tree: {box_label}**")

    for i, ch in enumerate(box_changes):
        icon  = TYPE_ICONS.get(ch["type"], "•")
        label = f"{icon} **{ch['type']}** — {ch['detail']}"
        col_label, col_btn = st.columns([5, 1])
        with col_label:
            st.markdown(label)
        with col_btn:
            btn_key = f"accept_{box_id}_{ch['type']}_{i}"
            if st.button("Accept", key=btn_key, use_container_width=True):
                accept_single_change(ch)
                reload_working_dataset()
                set_status(f"Accepted: {ch['type']} — {ch['detail']}", "success")
                st.rerun()

    st.markdown("")  # spacing between boxes

# ── Side-by-side JSON ────────────────────────────────────────────────────────
with st.expander("Side-by-side JSON (original vs live)"):
    left, right = st.columns(2)
    with left:
        st.markdown("**Original (permanent)**")
        st.json(original)
    with right:
        st.markdown("**Live (working)**")
        st.json(working)

render_status_banner()
render_site_footer()
