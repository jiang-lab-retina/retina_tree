"""Minimalist logo and site chrome for Retina Trees."""

from __future__ import annotations

import html
from pathlib import Path

LOGO_PATH = Path(__file__).resolve().parent / "assets" / "logo.svg"
BRAND_NAME = "Retina Trees"
BRAND_TAGLINE = "Academic lineage explorer"


def logo_svg(*, size: int = 40, css_class: str = "rt-logo-svg") -> str:
    raw = LOGO_PATH.read_text(encoding="utf-8")
    return raw.replace(
        "<svg ",
        f'<svg class="{css_class}" width="{size}" height="{size}" ',
        1,
    )


def brand_mark_html(*, size: int = 40) -> str:
    return f'<span class="rt-logo-wrap" aria-hidden="true">{logo_svg(size=size)}</span>'


def render_ambient_decor() -> str:
    """Fixed background accents (call once per page via markdown)."""
    return """
    <div class="rt-ambient" aria-hidden="true">
      <span class="rt-ambient-orb rt-ambient-orb--tr"></span>
      <span class="rt-ambient-orb rt-ambient-orb--bl"></span>
      <span class="rt-ambient-grid"></span>
    </div>
    """


def render_brand_row(
    *,
    title: str | None = None,
    subtitle: str | None = None,
    show_tagline: bool = True,
    logo_size: int = 44,
) -> str:
    safe_title = html.escape(title or BRAND_NAME)
    tagline = (
        f'<p class="rt-brand-tagline">{html.escape(BRAND_TAGLINE)}</p>'
        if show_tagline and not subtitle
        else ""
    )
    subtitle_html = (
        f'<p class="rt-brand-subtitle">{html.escape(subtitle)}</p>' if subtitle else ""
    )
    return f"""
    <div class="rt-brand-row">
      {brand_mark_html(size=logo_size)}
      <div class="rt-brand-copy">
        <p class="rt-brand-eyebrow">{html.escape(BRAND_NAME)}</p>
        <h1 class="rt-brand-title">{safe_title}</h1>
        {tagline}
        {subtitle_html}
      </div>
    </div>
  """


def render_section_rule(*, label: str | None = None) -> str:
    if label:
        safe = html.escape(label)
        return f'<div class="rt-section-rule"><span>{safe}</span></div>'
    return '<div class="rt-section-rule rt-section-rule--plain"></div>'


def site_footer_html() -> str:
    return f"""
    <footer class="rt-site-footer" aria-hidden="true">
      <span class="rt-footer-mark">{logo_svg(size=22)}</span>
      <span class="rt-footer-text">{html.escape(BRAND_NAME)}</span>
      <span class="rt-footer-dot"></span>
      <span class="rt-footer-muted">lineage trees</span>
    </footer>
    """
