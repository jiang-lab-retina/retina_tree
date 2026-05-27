"""Google sign-in (Streamlit OIDC) and role checks."""

from __future__ import annotations

from typing import Any

import streamlit as st


def auth_is_configured() -> bool:
    try:
        auth = st.secrets.get("auth")
        if not auth:
            return False
        if auth.get("client_id") and auth.get("client_secret"):
            return True
        google = auth.get("google")
        if isinstance(google, dict) and google.get("client_id") and google.get("client_secret"):
            return True
    except (FileNotFoundError, AttributeError, KeyError):
        return False
    return False


def get_admin_emails() -> set[str]:
    emails: set[str] = set()
    try:
        app_cfg = st.secrets.get("app", {})
        if isinstance(app_cfg, dict):
            raw = app_cfg.get("admin_emails", [])
            if isinstance(raw, str):
                emails.update(e.strip().lower() for e in raw.split(",") if e.strip())
            elif isinstance(raw, list):
                emails.update(str(e).strip().lower() for e in raw if str(e).strip())
    except (FileNotFoundError, AttributeError, KeyError):
        pass
    return emails


def dev_mode_enabled() -> bool:
    try:
        app_cfg = st.secrets.get("app", {})
        return bool(app_cfg.get("allow_dev_login", False)) if isinstance(app_cfg, dict) else False
    except (FileNotFoundError, AttributeError, KeyError):
        return False


def _init_dev_user_state() -> None:
    if "dev_user_email" not in st.session_state:
        st.session_state.dev_user_email = ""
        st.session_state.dev_user_name = ""


def is_logged_in() -> bool:
    if auth_is_configured():
        return bool(getattr(st.user, "is_logged_in", False))
    if dev_mode_enabled():
        return bool(st.session_state.get("dev_user_email"))
    return False


def current_user_email() -> str | None:
    if auth_is_configured() and getattr(st.user, "is_logged_in", False):
        email = getattr(st.user, "email", None)
        return str(email).strip().lower() if email else None
    if dev_mode_enabled():
        email = st.session_state.get("dev_user_email", "")
        return str(email).strip().lower() if email else None
    return None


def current_user_name() -> str | None:
    if auth_is_configured() and getattr(st.user, "is_logged_in", False):
        name = getattr(st.user, "name", None) or getattr(st.user, "email", None)
        return str(name) if name else None
    if dev_mode_enabled():
        return st.session_state.get("dev_user_name") or st.session_state.get("dev_user_email")
    return None


def is_admin() -> bool:
    email = current_user_email()
    if not email:
        return False
    return email in get_admin_emails()


def render_login_gate(*, message: str = "Sign in with Google to continue.") -> None:
    """Block the page until the user is authenticated."""
    if is_logged_in():
        return

    st.markdown(
        f"""
        <div class="apple-hero">
          <h1>Sign in required</h1>
          <p class="subtitle">{message}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if auth_is_configured():
        if st.button("Sign in with Google", type="primary", use_container_width=False):
            st.login("google")
        st.caption("Use your lab Google account. Edits are submitted for administrator approval.")
        st.stop()

    if dev_mode_enabled():
        _init_dev_user_state()
        st.warning("Google auth is not configured. Dev sign-in is enabled for local testing only.")
        with st.form("dev_login"):
            email = st.text_input("Email", placeholder="you@university.edu")
            name = st.text_input("Display name (optional)")
            if st.form_submit_button("Continue (dev)", use_container_width=True):
                if not email.strip():
                    st.error("Email is required.")
                else:
                    st.session_state.dev_user_email = email.strip().lower()
                    st.session_state.dev_user_name = name.strip() or email.strip()
                    st.rerun()
        st.stop()

    st.error(
        "Authentication is not configured. Add Google OAuth settings to `.streamlit/secrets.toml` "
        "(see `.streamlit/secrets.toml.example`)."
    )
    st.stop()


def render_admin_gate() -> None:
    render_login_gate(message="Sign in with your administrator Google account.")
    if not is_admin():
        st.error("This page is restricted to administrators.")
        st.page_link("app.py", label="← Back to trees", icon="🌳")
        st.stop()


def render_account_bar() -> None:
    """Compact account info for page headers."""
    if not is_logged_in():
        if auth_is_configured():
            if st.button("Sign in", key="header_sign_in"):
                st.login("google")
        return

    email = current_user_email() or "unknown"
    name = current_user_name() or email
    role = "Administrator" if is_admin() else "Contributor"
    pending = ""
    try:
        from retina_tree.proposals_db import count_pending

        n = count_pending(user_email=email)
        if n:
            pending = f" · {n} pending submission{'s' if n != 1 else ''}"
    except Exception:
        pass

    col1, col2 = st.columns([5, 1])
    with col1:
        st.caption(f"Signed in as **{name}** ({role}){pending}")
    with col2:
        if auth_is_configured() and getattr(st.user, "is_logged_in", False):
            if st.button("Sign out", key="header_sign_out", type="secondary"):
                st.logout()
        elif dev_mode_enabled() and st.session_state.get("dev_user_email"):
            if st.button("Sign out", key="header_dev_sign_out", type="secondary"):
                st.session_state.dev_user_email = ""
                st.session_state.dev_user_name = ""
                st.rerun()


def submit_edit_proposal(
    *,
    action: str,
    box_id: str,
    box_title: str,
    payload: dict[str, Any],
    summary: str,
) -> str:
    from retina_tree.proposals_db import create_proposal

    email = current_user_email()
    if not email:
        raise RuntimeError("Must be signed in to submit edits.")

    return create_proposal(
        user_email=email,
        user_name=current_user_name(),
        action=action,
        box_id=box_id,
        box_title=box_title,
        payload=payload,
        summary=summary,
    )
