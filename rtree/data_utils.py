"""Load, normalize, and serialize retina tree JSON datasets."""

from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

DEFAULT_JSON_PATH = Path(__file__).resolve().parent.parent / "data" / "retina_trees_data.json"


def slugify_id(value: str) -> str:
    base = re.sub(r"[^A-Z0-9]+", "_", str(value or "").upper()).strip("_")
    return base or "NODE"


def normalize_nodes(raw_nodes: Any) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    seen: set[str] = set()

    if isinstance(raw_nodes, list):
        for raw_node in raw_nodes:
            if not isinstance(raw_node, dict):
                continue
            node_id = str(raw_node.get("id") or "").strip()
            if not node_id or node_id in seen:
                continue
            label = str(raw_node.get("label") or node_id).strip() or node_id
            node: dict[str, Any] = {"id": node_id, "label": label}
            if "pubmed" in raw_node:
                node["pubmed"] = raw_node["pubmed"]
            nodes.append(node)
            seen.add(node_id)
    elif isinstance(raw_nodes, dict):
        for node_id, label in raw_nodes.items():
            clean_id = str(node_id or "").strip()
            if not clean_id or clean_id in seen:
                continue
            clean_label = str(label or clean_id).strip() or clean_id
            nodes.append({"id": clean_id, "label": clean_label})
            seen.add(clean_id)

    return nodes


def normalize_links(raw_links: Any, node_map: dict[str, str]) -> list[dict[str, str]]:
    links: list[dict[str, str]] = []
    seen: set[str] = set()

    if not isinstance(raw_links, list):
        return links

    for raw_link in raw_links:
        parent = ""
        child = ""
        if isinstance(raw_link, (list, tuple)) and len(raw_link) >= 2:
            parent, child = raw_link[0], raw_link[1]
        elif isinstance(raw_link, dict):
            parent = raw_link.get("parent", "")
            child = raw_link.get("child", "")

        parent = str(parent or "").strip()
        child = str(child or "").strip()
        if (
            not parent
            or not child
            or parent not in node_map
            or child not in node_map
            or parent == child
        ):
            continue

        key = f"{parent}->{child}"
        if key in seen:
            continue
        links.append({"parent": parent, "child": child})
        seen.add(key)

    return links


def normalize_dataset(raw_data: Any) -> dict[str, Any]:
    dataset = {
        "version": int(raw_data.get("version", 1)) if isinstance(raw_data, dict) else 1,
        "title": str(raw_data.get("title", "Retina Tree")) if isinstance(raw_data, dict) else "Retina Tree",
        "boxes": [],
    }

    if not isinstance(raw_data, dict) or not isinstance(raw_data.get("boxes"), list):
        return dataset

    for index, raw_box in enumerate(raw_data["boxes"]):
        nodes = normalize_nodes(raw_box.get("nodes") if isinstance(raw_box, dict) else None)
        node_map = {node["id"]: node["label"] for node in nodes}
        links = normalize_links(raw_box.get("links") if isinstance(raw_box, dict) else None, node_map)
        box_id = str((raw_box or {}).get("id") or f"box-{index + 1:02d}").strip()
        title = str((raw_box or {}).get("title") or f"Box {index + 1}").strip() or f"Box {index + 1}"
        dataset["boxes"].append(
            {
                "id": box_id,
                "title": title,
                "nodes": nodes,
                "links": links,
            }
        )

    return dataset


def serialize_dataset(dataset: dict[str, Any]) -> str:
    boxes_out = []
    for box in dataset.get("boxes", []):
        nodes_out: list[dict[str, Any]] = []
        for node in box.get("nodes", []):
            item: dict[str, Any] = {"id": node["id"], "label": node["label"]}
            if "pubmed" in node:
                item["pubmed"] = node["pubmed"]
            nodes_out.append(item)

        boxes_out.append(
            {
                "id": box["id"],
                "title": box["title"],
                "nodes": nodes_out,
                "links": [[link["parent"], link["child"]] for link in box.get("links", [])],
            }
        )

    payload = {
        "version": dataset.get("version", 1),
        "title": dataset.get("title", "Retina Tree"),
        "boxes": boxes_out,
    }
    return json.dumps(payload, indent=2) + "\n"


def derive_box(box: dict[str, Any]) -> dict[str, Any]:
    labels = {node["id"]: node["label"] for node in box["nodes"]}
    children = {node["id"]: [] for node in box["nodes"]}
    indegree = {node["id"]: 0 for node in box["nodes"]}

    for link in box.get("links", []):
        parent = link["parent"]
        child = link["child"]
        if parent not in children or child not in labels:
            continue
        children[parent].append(child)
        indegree[child] = indegree.get(child, 0) + 1

    roots = [node["id"] for node in box["nodes"] if indegree.get(node["id"], 0) == 0]
    if not roots and box["nodes"]:
        roots = [box["nodes"][0]["id"]]

    return {
        **box,
        "labels": labels,
        "children": children,
        "indegree": indegree,
        "roots": roots,
        "node_count": len(box["nodes"]),
        "edge_count": len(box.get("links", [])),
    }


def load_dataset_from_path(path: Path | str = DEFAULT_JSON_PATH) -> dict[str, Any]:
    text = Path(path).read_text(encoding="utf-8")
    return normalize_dataset(json.loads(text))


def load_dataset_from_text(text: str) -> dict[str, Any]:
    return normalize_dataset(json.loads(text))


def get_current_box(dataset: dict[str, Any], current_box_id: str | None) -> dict[str, Any] | None:
    boxes = dataset.get("boxes", [])
    if not boxes:
        return None
    if current_box_id:
        for box in boxes:
            if box["id"] == current_box_id:
                return box
    return boxes[0]


def unique_node_id(box: dict[str, Any], candidate: str) -> str:
    used = {node["id"] for node in box["nodes"]}
    if candidate not in used:
        return candidate
    suffix = 2
    while f"{candidate}_{suffix}" in used:
        suffix += 1
    return f"{candidate}_{suffix}"


def clone_dataset(dataset: dict[str, Any]) -> dict[str, Any]:
    return deepcopy(dataset)


def find_box_by_title(dataset: dict[str, Any], title: str) -> dict[str, Any] | None:
    target = str(title or "").strip().lower()
    if not target:
        return None
    for box in dataset.get("boxes", []):
        if str(box.get("title", "")).strip().lower() == target:
            return box
    return None


def unique_box_id(dataset: dict[str, Any], candidate: str) -> str:
    used = {box["id"] for box in dataset.get("boxes", [])}
    if candidate not in used:
        return candidate
    suffix = 2
    while f"{candidate}_{suffix}" in used:
        suffix += 1
    return f"{candidate}_{suffix}"


def get_or_create_box(dataset: dict[str, Any], title: str) -> dict[str, Any]:
    """Return the box matching ``title`` (case-insensitive) or create a new one."""
    existing = find_box_by_title(dataset, title)
    if existing is not None:
        return existing
    clean_title = str(title or "").strip() or "New tree"
    box = {
        "id": unique_box_id(dataset, slugify_id(clean_title).lower() or "box"),
        "title": clean_title,
        "nodes": [],
        "links": [],
    }
    dataset.setdefault("boxes", []).append(box)
    return box


def get_or_create_node(box: dict[str, Any], name: str) -> str:
    """Return the id of the node whose label matches ``name``; create it if absent."""
    clean = str(name or "").strip()
    if not clean:
        raise ValueError("Name cannot be empty.")
    target = clean.lower()
    for node in box["nodes"]:
        if str(node.get("label", "")).strip().lower() == target:
            return node["id"]
        if str(node.get("id", "")).strip().lower() == target:
            return node["id"]
    new_id = unique_node_id(box, slugify_id(clean))
    box["nodes"].append({"id": new_id, "label": clean})
    return new_id


def add_link(box: dict[str, Any], parent_id: str, child_id: str) -> bool:
    """Add a parent→child link if valid and not already present. Returns True if added."""
    if not parent_id or not child_id or parent_id == child_id:
        return False
    for link in box.get("links", []):
        if link["parent"] == parent_id and link["child"] == child_id:
            return False
    box.setdefault("links", []).append({"parent": parent_id, "child": child_id})
    return True
