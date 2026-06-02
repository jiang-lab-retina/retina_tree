"""Original (permanent) and working (live) dataset copies on disk."""

from __future__ import annotations

import json
import shutil
from copy import deepcopy
from pathlib import Path

from rtree.data_utils import (
    DEFAULT_JSON_PATH,
    load_dataset_from_path,
    normalize_dataset,
    serialize_dataset,
)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SEED_JSON_PATH = DEFAULT_JSON_PATH
ORIGINAL_JSON_PATH = DATA_DIR / "original_dataset.json"
WORKING_JSON_PATH = DATA_DIR / "working_dataset.json"


def ensure_datasets_exist() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not ORIGINAL_JSON_PATH.exists():
        if SEED_JSON_PATH.exists():
            shutil.copy2(SEED_JSON_PATH, ORIGINAL_JSON_PATH)
        else:
            ORIGINAL_JSON_PATH.write_text(
                serialize_dataset(normalize_dataset({"version": 1, "title": "Retina Tree", "boxes": []})),
                encoding="utf-8",
            )
    if not WORKING_JSON_PATH.exists():
        shutil.copy2(ORIGINAL_JSON_PATH, WORKING_JSON_PATH)


def load_original_dataset() -> dict:
    ensure_datasets_exist()
    return load_dataset_from_path(ORIGINAL_JSON_PATH)


def load_working_dataset() -> dict:
    ensure_datasets_exist()
    return load_dataset_from_path(WORKING_JSON_PATH)


def save_original_dataset(dataset: dict) -> None:
    ensure_datasets_exist()
    ORIGINAL_JSON_PATH.write_text(serialize_dataset(dataset), encoding="utf-8")


def save_working_dataset(dataset: dict) -> None:
    ensure_datasets_exist()
    WORKING_JSON_PATH.write_text(serialize_dataset(dataset), encoding="utf-8")


def has_pending_changes() -> bool:
    original = load_original_dataset()
    working = load_working_dataset()
    return serialize_dataset(original) != serialize_dataset(working)


def accept_all_changes() -> None:
    """Make working data permanent (original ← working)."""
    working = load_working_dataset()
    save_original_dataset(deepcopy(working))


def reject_all_changes() -> None:
    """Revert live data to last permanent original (working ← original)."""
    original = load_original_dataset()
    save_working_dataset(deepcopy(original))


def apply_single_change(original: dict, working: dict, change: dict) -> None:
    """Apply exactly one change from *working* onto *original* in-place."""
    box_id      = change.get("box_id", "")
    change_type = change.get("type", "")
    node_id     = change.get("node_id", "")
    parent_id   = change.get("parent_id", "")
    child_id    = change.get("child_id", "")

    orig_by_id = {box["id"]: box for box in original.get("boxes", [])}
    work_by_id = {box["id"]: box for box in working.get("boxes", [])}
    orig_box   = orig_by_id.get(box_id)
    work_box   = work_by_id.get(box_id)

    if change_type == "Box renamed":
        if orig_box and work_box:
            orig_box["title"] = work_box["title"]

    elif change_type == "Node added":
        if orig_box is not None and work_box:
            work_node = next((n for n in work_box["nodes"] if n["id"] == node_id), None)
            if work_node and not any(n["id"] == node_id for n in orig_box.get("nodes", [])):
                orig_box.setdefault("nodes", []).append(deepcopy(work_node))
        elif orig_box is None and work_box:
            # Whole box is new — add the box with just this node
            new_box: dict = {
                "id": box_id,
                "title": work_box.get("title", box_id),
                "nodes": [],
                "links": [],
            }
            work_node = next((n for n in work_box["nodes"] if n["id"] == node_id), None)
            if work_node:
                new_box["nodes"].append(deepcopy(work_node))
            original.setdefault("boxes", []).append(new_box)

    elif change_type == "Node renamed":
        if orig_box and work_box:
            work_node = next((n for n in work_box["nodes"] if n["id"] == node_id), None)
            orig_node = next((n for n in orig_box.get("nodes", []) if n["id"] == node_id), None)
            if work_node and orig_node:
                orig_node["label"] = work_node["label"]

    elif change_type == "Node removed":
        if orig_box:
            orig_box["nodes"] = [n for n in orig_box.get("nodes", []) if n["id"] != node_id]
            # Also remove dangling links
            orig_box["links"] = [
                lnk for lnk in orig_box.get("links", [])
                if lnk["parent"] != node_id and lnk["child"] != node_id
            ]

    elif change_type == "Link added":
        if orig_box is not None:
            existing = {(lnk["parent"], lnk["child"]) for lnk in orig_box.get("links", [])}
            if (parent_id, child_id) not in existing:
                orig_box.setdefault("links", []).append({"parent": parent_id, "child": child_id})

    elif change_type == "Link removed":
        if orig_box:
            orig_box["links"] = [
                lnk for lnk in orig_box.get("links", [])
                if not (lnk["parent"] == parent_id and lnk["child"] == child_id)
            ]


def accept_single_change(change: dict) -> None:
    """Load datasets, apply one change to original, and save."""
    original = load_original_dataset()
    working  = load_working_dataset()
    apply_single_change(original, working, change)
    save_original_dataset(original)
