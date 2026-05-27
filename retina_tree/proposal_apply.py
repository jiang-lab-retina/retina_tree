"""Apply approved edit proposals to the canonical dataset."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from retina_tree.data_utils import get_current_box, slugify_id, unique_node_id


def describe_proposal(proposal: dict[str, Any]) -> str:
    return proposal.get("summary") or proposal.get("action", "edit")


def apply_proposal(dataset: dict[str, Any], proposal: dict[str, Any]) -> dict[str, Any]:
    """Return a new dataset with one proposal applied. Raises ValueError on invalid ops."""
    data = deepcopy(dataset)
    action = proposal["action"]
    payload = proposal["payload"]
    box_id = proposal["box_id"]

    box = None
    for candidate in data.get("boxes", []):
        if candidate["id"] == box_id:
            box = candidate
            break
    if box is None:
        raise ValueError(f"Unknown box id: {box_id}")

    if action == "add_node":
        label = str(payload.get("label", "")).strip()
        if not label:
            raise ValueError("Node label is required.")
        requested_id = str(payload.get("node_id") or "").strip() or slugify_id(label)
        node_id = unique_node_id(box, requested_id)
        node: dict[str, Any] = {"id": node_id, "label": label}
        if payload.get("pubmed"):
            node["pubmed"] = payload["pubmed"]
        box["nodes"].append(node)

    elif action == "update_node":
        node_id = str(payload.get("node_id", "")).strip()
        label = str(payload.get("label", "")).strip()
        if not node_id or not label:
            raise ValueError("Node id and label are required.")
        target = next((n for n in box["nodes"] if n["id"] == node_id), None)
        if target is None:
            raise ValueError(f"Node not found: {node_id}")
        target["label"] = label

    elif action == "delete_node":
        node_id = str(payload.get("node_id", "")).strip()
        if not node_id:
            raise ValueError("Node id is required.")
        box["nodes"] = [n for n in box["nodes"] if n["id"] != node_id]
        box["links"] = [
            link
            for link in box["links"]
            if link["parent"] != node_id and link["child"] != node_id
        ]

    elif action == "add_link":
        parent = str(payload.get("parent", "")).strip()
        child = str(payload.get("child", "")).strip()
        if not parent or not child:
            raise ValueError("Parent and child are required.")
        if parent == child:
            raise ValueError("Parent and child must differ.")
        if any(link["parent"] == parent and link["child"] == child for link in box["links"]):
            raise ValueError("Link already exists.")
        box["links"].append({"parent": parent, "child": child})

    elif action == "delete_link":
        parent = str(payload.get("parent", "")).strip()
        child = str(payload.get("child", "")).strip()
        box["links"] = [
            link
            for link in box["links"]
            if not (link["parent"] == parent and link["child"] == child)
        ]

    else:
        raise ValueError(f"Unsupported action: {action}")

    return data


def build_summary(action: str, payload: dict[str, Any], box_title: str) -> str:
    if action == "add_node":
        return f"[{box_title}] Add node “{payload.get('label', '')}”"
    if action == "update_node":
        return f"[{box_title}] Rename node {payload.get('node_id', '')} → “{payload.get('label', '')}”"
    if action == "delete_node":
        return f"[{box_title}] Delete node {payload.get('node_id', '')}"
    if action == "add_link":
        return f"[{box_title}] Link {payload.get('parent', '')} → {payload.get('child', '')}"
    if action == "delete_link":
        return f"[{box_title}] Remove link {payload.get('parent', '')} → {payload.get('child', '')}"
    return f"[{box_title}] {action}"
