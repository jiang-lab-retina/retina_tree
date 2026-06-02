"""Diff original vs working datasets for administrator review."""

from __future__ import annotations

from typing import Any


def _node_map(box: dict) -> dict[str, dict]:
    return {node["id"]: node for node in box.get("nodes", [])}


def _link_set(box: dict) -> set[tuple[str, str]]:
    return {(link["parent"], link["child"]) for link in box.get("links", [])}


def diff_box(original: dict, working: dict) -> list[dict[str, str]]:
    """Human-readable change rows for one tree box.

    Each row includes machine-readable fields (``box_id``, ``node_id``,
    ``parent_id``, ``child_id``) so individual changes can be accepted or
    rejected without reprocessing the full diff.
    """
    lines: list[dict[str, str]] = []
    box_id    = working.get("id") or original.get("id", "")
    box_title = working.get("title") or original.get("title") or box_id

    # ── box title rename ──────────────────────────────────────────────────
    orig_title = original.get("title", "")
    work_title = working.get("title", "")
    if orig_title and work_title and orig_title != work_title:
        lines.append({
            "type":     "Box renamed",
            "detail":   f'"{orig_title}" \u2192 "{work_title}"',
            "box":      work_title,
            "box_id":   box_id,
            "node_id":  "",
            "parent_id": "",
            "child_id":  "",
        })

    orig_nodes = _node_map(original)
    work_nodes = _node_map(working)
    orig_links = _link_set(original)
    work_links = _link_set(working)

    # ── node changes ──────────────────────────────────────────────────────
    for node_id, node in work_nodes.items():
        if node_id not in orig_nodes:
            lines.append({
                "type":      "Node added",
                "detail":    f"{node['label']} ({node_id})",
                "box":       box_title,
                "box_id":    box_id,
                "node_id":   node_id,
                "parent_id": "",
                "child_id":  "",
            })
        elif orig_nodes[node_id].get("label") != node.get("label"):
            lines.append({
                "type":    "Node renamed",
                "detail":  (
                    f"{node_id}: \u201c{orig_nodes[node_id]['label']}\u201d"
                    f" \u2192 \u201c{node['label']}\u201d"
                ),
                "box":      box_title,
                "box_id":   box_id,
                "node_id":  node_id,
                "parent_id": "",
                "child_id":  "",
            })

    for node_id, node in orig_nodes.items():
        if node_id not in work_nodes:
            lines.append({
                "type":      "Node removed",
                "detail":    f"{node['label']} ({node_id})",
                "box":       box_title,
                "box_id":    box_id,
                "node_id":   node_id,
                "parent_id": "",
                "child_id":  "",
            })

    # ── link changes ──────────────────────────────────────────────────────
    for parent, child in work_links - orig_links:
        pl = work_nodes.get(parent, {}).get("label", parent)
        cl = work_nodes.get(child,  {}).get("label", child)
        lines.append({
            "type":      "Link added",
            "detail":    f"{pl} ({parent}) \u2192 {cl} ({child})",
            "box":       box_title,
            "box_id":    box_id,
            "node_id":   "",
            "parent_id": parent,
            "child_id":  child,
        })

    for parent, child in orig_links - work_links:
        pl = orig_nodes.get(parent, {}).get("label", parent)
        cl = orig_nodes.get(child,  {}).get("label", child)
        lines.append({
            "type":      "Link removed",
            "detail":    f"{pl} ({parent}) \u2192 {cl} ({child})",
            "box":       box_title,
            "box_id":    box_id,
            "node_id":   "",
            "parent_id": parent,
            "child_id":  child,
        })

    return lines


def diff_datasets(original: dict[str, Any], working: dict[str, Any]) -> list[dict[str, str]]:
    orig_by_id = {box["id"]: box for box in original.get("boxes", [])}
    work_by_id = {box["id"]: box for box in working.get("boxes", [])}
    all_ids = list(dict.fromkeys([*orig_by_id.keys(), *work_by_id.keys()]))

    rows: list[dict[str, str]] = []
    for box_id in all_ids:
        orig_box = orig_by_id.get(box_id, {"id": box_id, "title": box_id, "nodes": [], "links": []})
        work_box = work_by_id.get(box_id, {"id": box_id, "title": box_id, "nodes": [], "links": []})
        rows.extend(diff_box(orig_box, work_box))
    return rows


def summarize_changes(original: dict[str, Any], working: dict[str, Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in diff_datasets(original, working):
        counts[row["type"]] = counts.get(row["type"], 0) + 1
    return counts
