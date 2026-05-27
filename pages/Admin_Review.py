"""Administrator review queue for proposed edits."""

from __future__ import annotations

import streamlit as st

from retina_tree.auth import current_user_email, render_account_bar, render_admin_gate
from retina_tree.dataset_store import load_approved_dataset, save_approved_dataset
from retina_tree.proposal_apply import apply_proposal
from retina_tree.proposals_db import (
    STATUS_APPROVED,
    STATUS_PENDING,
    STATUS_REJECTED,
    count_pending,
    get_proposal,
    list_proposals,
    set_proposal_status,
)
from retina_tree.ui import (
    configure_page,
    ensure_dataset_loaded,
    inject_apple_theme,
    reload_approved_dataset,
    render_page_header,
    render_status_banner,
    set_status,
)

configure_page(title="Admin Review · Retina Trees", icon="🛡️")
inject_apple_theme()
ensure_dataset_loaded()
render_admin_gate()

render_page_header(
    subtitle="Review contributor proposals. Approved changes update the public dataset immediately."
)
render_account_bar()

pending_count = count_pending()
st.metric("Pending proposals", pending_count)

pending = list_proposals(status=STATUS_PENDING, limit=100)
if not pending:
    st.success("No pending proposals. The queue is clear.")
    st.page_link("app.py", label="← Back to trees", icon="🌳")
    st.stop()

st.markdown('<p class="apple-section-label">Review queue</p>', unsafe_allow_html=True)

for proposal in pending:
    with st.container(border=True):
        st.markdown(f"**{proposal['summary']}**")
        st.caption(
            f"Submitted {proposal['created_at'][:19].replace('T', ' ')} UTC · "
            f"{proposal['user_name'] or proposal['user_email']} · "
            f"Box `{proposal['box_id']}` · ID `{proposal['id'][:8]}…`"
        )
        st.json(proposal["payload"])

        note = st.text_input(
            "Review note (optional)",
            key=f"note_{proposal['id']}",
            placeholder="Reason for rejection or internal note",
        )

        approve_col, reject_col, spacer = st.columns([1, 1, 2])
        with approve_col:
            if st.button("Approve", key=f"approve_{proposal['id']}", use_container_width=True):
                fresh = get_proposal(proposal["id"])
                if fresh is None or fresh["status"] != STATUS_PENDING:
                    set_status("Proposal is no longer pending.", "warning")
                    st.rerun()

                try:
                    dataset = load_approved_dataset()
                    updated = apply_proposal(dataset, fresh)
                    save_approved_dataset(updated)
                    admin_email = current_user_email() or "admin"
                    set_proposal_status(
                        proposal["id"],
                        status=STATUS_APPROVED,
                        reviewed_by=admin_email,
                        review_note=note.strip() or None,
                    )
                    reload_approved_dataset()
                    set_status(f"Approved and published: {proposal['summary']}", "success")
                    st.rerun()
                except (ValueError, KeyError) as exc:
                    set_status(f"Could not apply proposal: {exc}", "error")

        with reject_col:
            if st.button("Reject", key=f"reject_{proposal['id']}", type="secondary", use_container_width=True):
                admin_email = current_user_email() or "admin"
                if set_proposal_status(
                    proposal["id"],
                    status=STATUS_REJECTED,
                    reviewed_by=admin_email,
                    review_note=note.strip() or "Rejected by administrator.",
                ):
                    set_status(f"Rejected: {proposal['summary']}", "success")
                    st.rerun()
                else:
                    set_status("Proposal is no longer pending.", "warning")
                    st.rerun()

st.divider()
st.markdown('<p class="apple-section-label">Recently reviewed</p>', unsafe_allow_html=True)
recent = [p for p in list_proposals(limit=30) if p["status"] != STATUS_PENDING][:15]
if recent:
    st.dataframe(
        [
            {
                "When": p["created_at"][:19].replace("T", " "),
                "Status": p["status"],
                "Change": p["summary"],
                "By": p["user_email"],
                "Reviewer": p.get("reviewed_by") or "—",
            }
            for p in recent
        ],
        use_container_width=True,
        hide_index=True,
    )

render_status_banner()
