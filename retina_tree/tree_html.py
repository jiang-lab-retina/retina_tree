"""Render interactive tree cards as HTML fragments for st.html (no iframe scrollbars)."""

from __future__ import annotations

import html
import json
from pathlib import Path

from retina_tree.data_utils import derive_box
from retina_tree.search import focus_in_subtree
from retina_tree.theme import APPLE_TREE_CSS

VIEWER_CSS_PATH = Path(__file__).resolve().parent / "viewer.css"
HORIZONTAL_TREE_CSS_PATH = Path(__file__).resolve().parent / "horizontal_tree.css"

# Scoped overrides when multiple cards share one Streamlit page (not isolated iframes).
EMBED_LAYOUT_CSS = """
.retina-tree-embed-outer {
  width: 100%;
  overflow-x: auto;
  overflow-y: visible;
  margin: 0 0 1rem;
  -webkit-overflow-scrolling: touch;
}

.retina-tree-embed {
  display: inline-block;
  width: max-content;
  min-width: 100%;
  margin: 0;
  overflow: visible;
  vertical-align: top;
}

.retina-tree-embed .tree-card {
  width: max-content;
  min-width: 100%;
  max-width: none;
  overflow: visible;
}

.retina-tree-embed .card-head {
  width: 100%;
  box-sizing: border-box;
}

.retina-tree-embed .card-body,
.retina-tree-embed .forest,
.retina-tree-embed .tree,
.retina-tree-embed .tree ul {
  width: max-content;
  max-width: none;
  overflow: visible;
}

.retina-tree-embed .card-body {
  max-height: none;
}

.retina-tree-embed .tree-node {
  flex-shrink: 0;
}

.retina-tree-embed .tree-node.search-hit .node-button,
.retina-tree-embed .tree-node.search-hit .node-leaf {
  border-color: rgba(0, 113, 227, 0.55);
  box-shadow: 0 0 0 2px rgba(0, 113, 227, 0.2);
}

.retina-tree-embed .tree-node.search-focus .node-button,
.retina-tree-embed .tree-node.search-focus .node-leaf {
  border-color: #0071e3;
  background: linear-gradient(180deg, #fff9eb, #ffe8a3);
  box-shadow: 0 0 0 3px rgba(0, 113, 227, 0.35);
  font-weight: 700;
}

.retina-tree-embed .tree-node.search-focus {
  scroll-margin: 2rem;
}
"""


def _escape(text: str) -> str:
    return html.escape(str(text), quote=True)


def _node_search_classes(
    node_id: str,
    *,
    focus_node_id: str | None,
    highlight_node_ids: set[str] | None,
) -> str:
    classes = []
    if highlight_node_ids and node_id in highlight_node_ids:
        classes.append("search-hit")
    if focus_node_id and node_id == focus_node_id:
        classes.append("search-focus")
    return (" " + " ".join(classes)) if classes else ""


def _should_collapse_node(
    box: dict,
    node_id: str,
    depth: int,
    *,
    view_mode: str,
    focus_node_id: str | None,
) -> bool:
    children = box["children"].get(node_id, [])
    if not children:
        return False
    if focus_node_id:
        return not focus_in_subtree(box, node_id, focus_node_id)
    if view_mode == "collapse-all":
        return True
    if view_mode == "roots-only":
        return depth > 0
    return False


def _render_node(
    box: dict,
    node_id: str,
    depth: int,
    path: set[str],
    view_mode: str,
    *,
    focus_node_id: str | None = None,
    highlight_node_ids: set[str] | None = None,
) -> str:
    children = box["children"].get(node_id, [])
    label = box["labels"].get(node_id, node_id)
    is_shared = box["indegree"].get(node_id, 0) > 1
    has_cycle = node_id in path
    search_classes = _node_search_classes(
        node_id, focus_node_id=focus_node_id, highlight_node_ids=highlight_node_ids
    )
    depth_attr = f' data-depth="{depth}" data-node-id="{_escape(node_id)}"'

    badge = '<span class="shared-badge">shared</span>' if is_shared else ""

    if children and not has_cycle:
        should_collapse = _should_collapse_node(
            box, node_id, depth, view_mode=view_mode, focus_node_id=focus_node_id
        )
        collapsed_class = " collapsed" if should_collapse else ""
        expanded = "false" if should_collapse else "true"

        child_html = "".join(
            _render_node(
                box,
                child_id,
                depth + 1,
                path | {node_id},
                view_mode,
                focus_node_id=focus_node_id,
                highlight_node_ids=highlight_node_ids,
            )
            for child_id in children
        )

        display_label = _escape(label)
        return (
            f'<li class="tree-node has-children{collapsed_class}{search_classes}"{depth_attr}>'
            f'<div class="node-row">'
            f'<button type="button" class="node-button" aria-expanded="{expanded}">'
            f'<span class="caret">▶</span>'
            f'<span class="node-text">{display_label}</span>{badge}'
            f"</button></div>"
            f"<ul>{child_html}</ul>"
            f"</li>"
        )

    display_label = _escape(f"{label} (cycle)" if has_cycle else label)
    return (
        f'<li class="tree-node leaf{search_classes}"{depth_attr}>'
        f'<div class="node-row">'
        f'<span class="node-leaf">'
        f'<span class="node-text">{display_label}</span>{badge}'
        f"</span></div>"
        f"</li>"
    )


def _card_interaction_script(card_id: str, focus_node_id: str | None = None) -> str:
    """Per-card expand/collapse; scoped by id (required when multiple trees on one page)."""
    safe_id = json.dumps(card_id)
    safe_focus = json.dumps(focus_node_id) if focus_node_id else "null"
    return f"""
<script>
(function() {{
  const card = document.getElementById({safe_id});
  if (!card) return;
  const focusNodeId = {safe_focus};

  function scrollToFocus() {{
    if (!focusNodeId) return;
    const target = card.querySelector('.tree-node[data-node-id="' + focusNodeId + '"]');
    if (!target) return;
    const outer = card.closest(".retina-tree-embed-outer");
    target.scrollIntoView({{ behavior: "smooth", block: "center", inline: "center" }});
    if (outer) {{
      const rect = target.getBoundingClientRect();
      const outerRect = outer.getBoundingClientRect();
      if (rect.left < outerRect.left || rect.right > outerRect.right) {{
        outer.scrollLeft += rect.left - outerRect.left - outer.clientWidth / 2 + rect.width / 2;
      }}
    }}
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
  }}

  card.querySelectorAll(".card-toolbar button").forEach((button) => {{
    button.addEventListener("click", () => applyTreeMode(button.dataset.mode));
  }});

  card.querySelectorAll(".node-button").forEach((button) => {{
    button.addEventListener("click", () => {{
      const node = button.closest(".tree-node");
      const collapsed = node.classList.toggle("collapsed");
      button.setAttribute("aria-expanded", String(!collapsed));
    }});
  }});

  if (focusNodeId) {{
    window.setTimeout(scrollToFocus, 120);
    window.setTimeout(scrollToFocus, 450);
  }}
}})();
</script>
"""


def render_tree_card_html(
    box: dict,
    *,
    current_box_id: str | None = None,
    view_mode: str = "roots-only",
    card_id: str | None = None,
    focus_node_id: str | None = None,
    highlight_node_ids: set[str] | None = None,
) -> str:
    derived = derive_box(box)
    card_id = card_id or derived["id"]
    is_current = derived["id"] == current_box_id
    is_large = derived["node_count"] >= 20

    roots_html = "".join(
        _render_node(
            derived,
            root_id,
            0,
            set(),
            view_mode,
            focus_node_id=focus_node_id if box.get("id") == (card_id or derived["id"]) else None,
            highlight_node_ids=highlight_node_ids,
        )
        for root_id in derived["roots"]
    )
    effective_focus = focus_node_id if box.get("id") == (card_id or derived["id"]) else None

    current_class = " current-box" if is_current else ""
    size_attr = ' data-size="large"' if is_large else ""

    css = (
        VIEWER_CSS_PATH.read_text(encoding="utf-8")
        + "\n"
        + APPLE_TREE_CSS
        + "\n"
        + EMBED_LAYOUT_CSS
        + "\n"
        + HORIZONTAL_TREE_CSS_PATH.read_text(encoding="utf-8")
    )

    return f"""<div class="retina-tree-embed-outer">
<div class="retina-tree-embed">
<style>{css}</style>
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
{_card_interaction_script(card_id, effective_focus)}
</div>
</div>"""


def estimate_card_height(box: dict, view_mode: str = "roots-only") -> int:
    """Legacy helper if iframe embedding is used elsewhere."""
    derived = derive_box(box)
    header = 118
    root_count = max(1, len(derived["roots"]))
    if view_mode in ("roots-only", "collapse-all"):
        rows = max(1, (root_count + 2) // 3)
        return min(720, max(168, header + rows * 52 + 16))
    depth = max(
        (
            _tree_depth(derived, root_id, 0, set())
            for root_id in derived["roots"]
        ),
        default=0,
    )
    return min(4000, max(280, header + (depth + 1) * 72))


def _tree_depth(derived: dict, node_id: str, depth: int, path: set[str]) -> int:
    if node_id in path:
        return depth
    children = derived["children"].get(node_id, [])
    if not children:
        return depth
    return max(_tree_depth(derived, child, depth + 1, path | {node_id}) for child in children)
