"""Render HTML fragments with Streamlit version compatibility (Cloud-safe)."""

from __future__ import annotations

import inspect

import streamlit as st


def streamlit_supports_tree_html() -> bool:
    """True when st.html accepts JS + content width (Streamlit 1.52+)."""
    html_fn = getattr(st, "html", None)
    if html_fn is None:
        return False
    params = inspect.signature(html_fn).parameters
    return "unsafe_allow_javascript" in params and "width" in params


def render_custom_html(body: str) -> None:
    """Render app chrome HTML (no JS). Prefer over markdown for nested divs."""
    html_fn = getattr(st, "html", None)
    if html_fn is not None:
        sig = inspect.signature(html_fn)
        kwargs: dict = {}
        if "width" in sig.parameters:
            kwargs["width"] = "stretch"
        if "unsafe_allow_javascript" in sig.parameters:
            kwargs["unsafe_allow_javascript"] = False
        try:
            html_fn(body, **kwargs)
            return
        except TypeError:
            html_fn(body)
            return
    st.markdown(body, unsafe_allow_html=True)


def render_html_fragment(body: str, *, height: int | None = None) -> None:
    """
    Render tree card HTML. Uses st.html on 1.52+; falls back to components.html.
    """
    html_fn = getattr(st, "html", None)
    if html_fn is not None:
        sig = inspect.signature(html_fn)
        kwargs: dict = {}
        if "unsafe_allow_javascript" in sig.parameters:
            kwargs["unsafe_allow_javascript"] = True
        if "width" in sig.parameters:
            kwargs["width"] = "stretch"
        try:
            html_fn(body, **kwargs)
            return
        except TypeError:
            html_fn(body)
            return

    import streamlit.components.v1 as components

    components.html(body, height=height or 480, scrolling=True)
