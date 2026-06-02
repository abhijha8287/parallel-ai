from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "parallel_ai.db"
SCHEMA_PATH = ROOT / "parallel_ai" / "data" / "schema.sql"


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    with get_connection() as connection:
        connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))


def save_decision(
    decision: str,
    option_a: str,
    option_b: str,
    profile: dict[str, Any],
    simulation: dict[str, Any],
    notes: str = "",
) -> int:
    init_db()
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO decisions
            (created_at, decision, option_a, option_b, profile_json, simulation_json, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now().isoformat(timespec="seconds"),
                decision,
                option_a,
                option_b,
                json.dumps(profile),
                json.dumps(simulation),
                notes,
            ),
        )
        return int(cursor.lastrowid)


def list_decisions() -> list[dict[str, Any]]:
    init_db()
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM decisions ORDER BY datetime(created_at) DESC"
        ).fetchall()
    return [_decode(row) for row in rows]


def delete_decision(decision_id: int) -> None:
    init_db()
    with get_connection() as connection:
        connection.execute("DELETE FROM decisions WHERE id = ?", (decision_id,))


def _decode(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    item["profile"] = json.loads(item.pop("profile_json"))
    item["simulation"] = json.loads(item.pop("simulation_json"))
    return item

