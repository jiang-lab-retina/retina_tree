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
                serialize_dataset(normalize_dataset({"version": 1, "title": "Retina Trees", "boxes": []})),
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
