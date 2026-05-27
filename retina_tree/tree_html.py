"""Render interactive tree cards as HTML for Streamlit components."""

from __future__ import annotations

import html
from pathlib import Path

from retina_tree.data_utils import derive_box
from retina_tree.theme import APPLE_TREE_CSS

VIEWER_CSS_PATH = Path(__file__).resolve().parent / "viewer.css"


def _escape(text: str) -> str:
    return html.escape(str(text), quote=True)


def _render_node(
    box: dict,
    node_id: str,
    depth: int,
    path: set[str],
    view_mode: str,
) -> str:
    children = box["children"].get(node_id, [])
    label = box["labels"].get(node_id, node_id)
    is_shared = box["indegree"].get(node_id, 0) > 1
    has_cycle = node_id in path
    next_path = set(path)
    depth_attr = f' data-depth="{depth}"'

    badge = '<span class="shared-badge">shared</span>' if is_shared else ""

    if children and not has_cycle:
        should_collapse = view_mode == "collapse-all" or (
            view_mode == "roots-only" and depth > 0
        )
        collapsed_class = " collapsed" if should_collapse else ""
        expanded = "false" if should_collapse else "true"

        child_html = "".join(
            _render_node(box, child_id, depth + 1, next_path | {node_id}, view_mode)
            for child_id in children
        )

        display_label = _escape(label)
        return (
            f'<li class="tree-node has-children{collapsed_class}"{depth_attr}>'
            f'<div class="node-row">'
            f'<button type="button" class="node-button" aria-expanded="{expanded}">'
            f'<span class="caret">▾</span>'
            f'<span class="node-text">{display_label}</span>{badge}'
            f"</button></div>"
            f"<ul>{child_html}</ul>"
            f"</li>"
        )

    display_label = _escape(f"{label} (cycle)" if has_cycle else label)
    return (
        f'<li class="tree-node leaf"{depth_attr}>'
        f'<div class="node-row">'
        f'<span class="node-leaf">'
        f'<span class="node-text">{display_label}</span>{badge}'
        f"</span></div>"
        f"</li>"
    )


def render_tree_card_html(
    box: dict,
    *,
    current_box_id: str | None = None,
    view_mode: str = "roots-only",
    card_id: str | None = None,
) -> str:
    derived = derive_box(box)
    card_id = card_id or derived["id"]
    is_current = derived["id"] == current_box_id
    is_large = derived["node_count"] >= 20

    roots_html = "".join(
        _render_node(derived, root_id, 0, set(), view_mode) for root_id in derived["roots"]
    )

    current_class = " current-box" if is_current else ""
    size_attr = ' data-size="large"' if is_large else ""

    css = VIEWER_CSS_PATH.read_text(encoding="utf-8") + "\n" + APPLE_TREE_CSS

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>{css}</style>
</head>
<body>
  <section class="tree-card{current_class}" id="{_escape(card_id)}"{size_attr}>
    <div class="card-head">
      <div class="card-title-row">
        <h2>{_escape(derived["title"])}</h2>
        <div class="meta">{derived["node_count"]} nodes · {derived["edge_count"]} links</div>
      </div>
      <div class="card-toolbar">
        <button type="button" data-mode="expand-all">Expand all</button>
        <button type="button" data-mode="collapse-all">Collapse all</button>
        <button type="button" data-mode="roots-only">Roots only</button>
      </div>
    </div>
    <div class="card-body">
      <div class="forest">
        <ul class="tree root-list">{roots_html}</ul>
      </div>
    </div>
  </section>
  <script>
    const card = document.querySelector(".tree-card");

    function measureContentHeight() {{
      const doc = document.documentElement;
      const body = document.body;
      return Math.ceil(
        Math.max(
          doc.scrollHeight,
          doc.offsetHeight,
          body.scrollHeight,
          body.offsetHeight,
          card.scrollHeight,
          card.offsetHeight
        )
      );
    }}

    function reportHeight() {{
      const height = Math.max(measureContentHeight(), 120);
      window.parent.postMessage({{ type: "streamlit:setFrameHeight", height }}, "*");
    }}

    function scheduleHeightReport() {{
      reportHeight();
      requestAnimationFrame(reportHeight);
      requestAnimationFrame(() => requestAnimationFrame(reportHeight));
      [50, 150, 350, 600].forEach((ms) => window.setTimeout(reportHeight, ms));
    }}

    function applyTreeMode(mode) {{
      card.querySelectorAll(".tree-node.has-children").forEach((node) => {{
        const depth = Number(node.dataset.depth || 0);
        let collapse = false;
        if (mode === "collapse-all") {{
          collapse = true;
        }} else if (mode === "roots-only") {{
          collapse = depth > 0;
        }}
        node.classList.toggle("collapsed", collapse);
        const button = node.querySelector(":scope > .node-row > .node-button");
        if (button) {{
          button.setAttribute("aria-expanded", String(!collapse));
        }}
      }});
      scheduleHeightReport();
    }}

    card.querySelectorAll(".card-toolbar button").forEach((button) => {{
      button.addEventListener("click", () => applyTreeMode(button.dataset.mode));
    }});

    card.querySelectorAll(".node-button").forEach((button) => {{
      button.addEventListener("click", () => {{
        const node = button.closest(".tree-node");
        const collapsed = node.classList.toggle("collapsed");
        button.setAttribute("aria-expanded", String(!collapsed));
        scheduleHeightReport();
      }});
    }});

    const forest = card.querySelector(".forest");
    if (typeof ResizeObserver !== "undefined") {{
      const observer = new ResizeObserver(scheduleHeightReport);
      observer.observe(card);
      if (forest) observer.observe(forest);
    }}
    scheduleHeightReport();
    window.addEventListener("load", scheduleHeightReport);
  </script>
</body>
</html>"""


def _max_tree_depth(derived: dict, node_id: str, depth: int, path: set[str]) -> int:
    if node_id in path:
        return depth
    children = derived["children"].get(node_id, [])
    if not children:
        return depth
    return max(_max_tree_depth(derived, child, depth + 1, path | {node_id}) for child in children)


def _tree_max_depth(derived: dict) -> int:
    if not derived["roots"]:
        return 0
    return max(_max_tree_depth(derived, root_id, 0, set()) for root_id in derived["roots"])


def estimate_card_height(box: dict, view_mode: str = "roots-only") -> int:
    """Initial iframe height; embedded script resizes to match visible tree."""
    derived = derive_box(box)
    header = 118
    root_count = max(1, len(derived["roots"]))

    if view_mode in ("roots-only", "collapse-all"):
        rows = max(1, (root_count + 2) // 3)
        return min(720, max(168, header + rows * 52 + 16))

    depth = _tree_max_depth(derived)
    # Expanded tree grows vertically by depth (~72px per level) plus root band
    expanded = header + (depth + 1) * 72 + root_count * 8
    return min(2400, max(280, expanded))
