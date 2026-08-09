import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("agent.db")

DB_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DB_DIR / "agent_memory.db"


def get_connection() -> sqlite3.Connection:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initialize SQLite database table for caller memory."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS caller_memory (
                user_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                language_preference TEXT DEFAULT 'English',
                facts TEXT NOT NULL,
                last_interaction TEXT NOT NULL
            );
            """
        )
        conn.commit()
    logger.info(f"Database initialized at {DB_PATH}")


def get_caller(user_id: str) -> Optional[dict[str, Any]]:
    """Retrieve caller profile by user_id."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_id, name, language_preference, facts, last_interaction FROM caller_memory WHERE user_id = ?",
            (user_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None

        facts_data = json.loads(row["facts"]) if row["facts"] else {}
        return {
            "user_id": row["user_id"],
            "name": row["name"],
            "language_preference": row["language_preference"],
            "facts": facts_data,
            "last_interaction": row["last_interaction"],
        }


def save_caller(
    user_id: str,
    name: str,
    language_preference: str = "English",
    facts: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Create or update caller profile in SQLite database."""
    init_db()
    facts = facts or {}
    facts_json = json.dumps(facts)
    now_iso = datetime.now(timezone.utc).isoformat()

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO caller_memory (user_id, name, language_preference, facts, last_interaction)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                name = excluded.name,
                language_preference = excluded.language_preference,
                facts = excluded.facts,
                last_interaction = excluded.last_interaction;
            """,
            (user_id, name, language_preference, facts_json, now_iso),
        )
        conn.commit()

    logger.info(f"Saved memory for caller {user_id} ({name})")
    return {
        "user_id": user_id,
        "name": name,
        "language_preference": language_preference,
        "facts": facts,
        "last_interaction": now_iso,
    }


def delete_caller(user_id: str) -> bool:
    """Delete caller profile from SQLite database (Forget Me tool)."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM caller_memory WHERE user_id = ?", (user_id,))
        conn.commit()
        deleted = cursor.rowcount > 0

    if deleted:
        logger.info(f"Deleted memory for caller {user_id}")
    return deleted
