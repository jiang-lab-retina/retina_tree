"""Fuzzy search across tree nodes."""

from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any


@dataclass(frozen=True)
class PersonMatch:
    box_id: str
    box_title: str
    node_id: str
    label: str
    score: float


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


def fuzzy_score(query: str, label: str, node_id: str) -> float:
    """Score in [0, 1]; higher is a better match."""
    q = _normalize(query)
    if not q:
        return 0.0

    label_n = _normalize(label)
    id_n = _normalize(node_id)
    combined = f"{label_n} {id_n}"

    if q == label_n or q == id_n:
        return 1.0
    if q in label_n or q in id_n:
        return 0.95

    tokens = [t for t in re.split(r"[\s,/]+", q) if t]
    if tokens and all(any(tok in part for part in (label_n, id_n, combined)) for tok in tokens):
        return 0.88

    ratio_label = SequenceMatcher(None, q, label_n).ratio()
    ratio_combined = SequenceMatcher(None, q, combined).ratio()
    partial = max(ratio_label, ratio_combined)

    # Substring sliding match boost (e.g. "dowl" → "Dowling")
    best_partial = partial
    if len(q) >= 3 and len(label_n) >= len(q):
        for i in range(len(label_n) - len(q) + 1):
            chunk = label_n[i : i + len(q)]
            best_partial = max(best_partial, SequenceMatcher(None, q, chunk).ratio() * 0.92)

    return best_partial


def search_dataset(
    dataset: dict[str, Any],
    query: str,
    *,
    min_score: float = 0.52,
    limit: int = 25,
) -> list[PersonMatch]:
    q = query.strip()
    if not q:
        return []

    matches: list[PersonMatch] = []
    for box in dataset.get("boxes", []):
        box_id = box.get("id", "")
        box_title = box.get("title", box_id)
        for node in box.get("nodes", []):
            node_id = str(node.get("id", "")).strip()
            label = str(node.get("label", node_id)).strip()
            if not node_id:
                continue
            score = fuzzy_score(q, label, node_id)
            if score >= min_score:
                matches.append(
                    PersonMatch(
                        box_id=box_id,
                        box_title=box_title,
                        node_id=node_id,
                        label=label,
                        score=score,
                    )
                )

    matches.sort(key=lambda m: (-m.score, m.label.lower()))
    return matches[:limit]


def build_parent_map(box: dict[str, Any]) -> dict[str, str]:
    parents: dict[str, str] = {}
    for link in box.get("links", []):
        parents[link["child"]] = link["parent"]
    return parents


def focus_in_subtree(derived: dict[str, Any], node_id: str, focus_id: str | None) -> bool:
    if not focus_id:
        return True
    if node_id == focus_id:
        return True
    for child_id in derived["children"].get(node_id, []):
        if focus_in_subtree(derived, child_id, focus_id):
            return True
    return False
