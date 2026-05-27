"""Canonical approved dataset on disk (separate from bundled seed JSON)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from retina_tree.data_utils import DEFAULT_JSON_PATH, load_dataset_from_path, normalize_dataset, serialize_dataset

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
APPROVED_JSON_PATH = DATA_DIR / "approved_dataset.json"
SEED_JSON_PATH = DEFAULT_JSON_PATH


def ensure_approved_dataset_exists() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not APPROVED_JSON_PATH.exists():
        if SEED_JSON_PATH.exists():
            shutil.copy2(SEED_JSON_PATH, APPROVED_JSON_PATH)
        else:
            APPROVED_JSON_PATH.write_text(
                serialize_dataset(normalize_dataset({"version": 1, "title": "Retina Trees", "boxes": []})),
                encoding="utf-8",
            )


def load_approved_dataset() -> dict:
    ensure_approved_dataset_exists()
    return load_dataset_from_path(APPROVED_JSON_PATH)


def save_approved_dataset(dataset: dict) -> None:
    ensure_approved_dataset_exists()
    APPROVED_JSON_PATH.write_text(serialize_dataset(dataset), encoding="utf-8")
