"""Optional password gate for the admin review page."""

from __future__ import annotations

import os

import streamlit as st

ENV_ADMIN_PASSWORD = "RETINA_TREE_ADMIN_PASSWORD"


def get_admin_password() -> str:
    """Password from environment (preferred) or Streamlit secrets — never from the repo."""
    env_password = os.environ.get(ENV_ADMIN_PASSWORD, "").strip()
    if env_password:
        return env_password

    try:
        app_cfg = st.secrets.get("app", {})
        if isinstance(app_cfg, dict):
            return str(app_cfg.get("admin_password", "")).strip()
    except Exception:
        pass
    return ""


def admin_password_configured() -> bool:
    return bool(get_admin_password())


def render_admin_access_gate() -> None:
    if not admin_password_configured():
        return

    if st.session_state.get("admin_unlocked"):
        return

    st.markdown(
        """
        <div class="apple-hero">
          <h1>Administrator access</h1>
          <p class="subtitle">Enter the admin password to review or publish changes.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("admin_unlock"):
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Unlock", use_container_width=True):
            if password == get_admin_password():
                st.session_state.admin_unlocked = True
                st.rerun()
            else:
                st.error("Incorrect password.")
    st.stop()
