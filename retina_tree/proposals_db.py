"""SQLite persistence for tracked edit proposals."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "proposals.db"

STATUS_PENDING = "pending"
STATUS_APPROVED = "approved"
STATUS_REJECTED = "rejected"


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS edit_proposals (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                user_email TEXT NOT NULL,
                user_name TEXT,
                action TEXT NOT NULL,
                box_id TEXT NOT NULL,
                box_title TEXT,
                payload TEXT NOT NULL,
                summary TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                reviewed_by TEXT,
                reviewed_at TEXT,
                review_note TEXT
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_proposals_status ON edit_proposals(status, created_at DESC)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_proposals_user ON edit_proposals(user_email, created_at DESC)"
        )
        conn.commit()


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def create_proposal(
    *,
    user_email: str,
    user_name: str | None,
    action: str,
    box_id: str,
    box_title: str | None,
    payload: dict[str, Any],
    summary: str,
) -> str:
    init_db()
    proposal_id = str(uuid4())
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO edit_proposals (
                id, created_at, user_email, user_name, action, box_id, box_title,
                payload, summary, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                proposal_id,
                _now_iso(),
                user_email,
                user_name,
                action,
                box_id,
                box_title,
                json.dumps(payload),
                summary,
                STATUS_PENDING,
            ),
        )
        conn.commit()
    return proposal_id


def list_proposals(*, status: str | None = None, user_email: str | None = None, limit: int = 200) -> list[dict[str, Any]]:
    init_db()
    clauses: list[str] = []
    params: list[Any] = []

    if status:
        clauses.append("status = ?")
        params.append(status)
    if user_email:
        clauses.append("user_email = ?")
        params.append(user_email)

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    query = f"SELECT * FROM edit_proposals {where} ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    with _connect() as conn:
        rows = conn.execute(query, params).fetchall()

    results: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["payload"] = json.loads(item["payload"])
        results.append(item)
    return results


def get_proposal(proposal_id: str) -> dict[str, Any] | None:
    init_db()
    with _connect() as conn:
        row = conn.execute("SELECT * FROM edit_proposals WHERE id = ?", (proposal_id,)).fetchone()
    if row is None:
        return None
    item = dict(row)
    item["payload"] = json.loads(item["payload"])
    return item


def count_pending(*, user_email: str | None = None) -> int:
    init_db()
    if user_email:
        query = "SELECT COUNT(*) FROM edit_proposals WHERE status = ? AND user_email = ?"
        params = (STATUS_PENDING, user_email)
    else:
        query = "SELECT COUNT(*) FROM edit_proposals WHERE status = ?"
        params = (STATUS_PENDING,)
    with _connect() as conn:
        return int(conn.execute(query, params).fetchone()[0])


def set_proposal_status(
    proposal_id: str,
    *,
    status: str,
    reviewed_by: str,
    review_note: str | None = None,
) -> bool:
    init_db()
    with _connect() as conn:
        cursor = conn.execute(
            """
            UPDATE edit_proposals
            SET status = ?, reviewed_by = ?, reviewed_at = ?, review_note = ?
            WHERE id = ? AND status = ?
            """,
            (status, reviewed_by, _now_iso(), review_note, proposal_id, STATUS_PENDING),
        )
        conn.commit()
        return cursor.rowcount > 0
