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
    """Initialize SQLite database tables for caller memory, outbound calls, and opt-out registry."""
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
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS outbound_calls (
                call_id TEXT PRIMARY KEY,
                phone_number TEXT NOT NULL,
                patient_name TEXT NOT NULL,
                reminder_type TEXT NOT NULL,
                status TEXT NOT NULL,
                retry_count INTEGER DEFAULT 0,
                next_retry_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS opt_out_registry (
                identifier TEXT PRIMARY KEY,
                opt_out_time TEXT NOT NULL,
                reason TEXT DEFAULT 'User requested opt-out during call'
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


# =============================================================================
# OUTBOUND CALL & OPT-OUT REGISTRY HELPER FUNCTIONS (DAY 6)
# =============================================================================


def is_opted_out(identifier: str) -> bool:
    """Check if a phone number or user_id is in the opt-out registry."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT identifier FROM opt_out_registry WHERE identifier = ?",
            (identifier,),
        )
        return cursor.fetchone() is not None


def register_opt_out(identifier: str, reason: str = "User requested opt-out during call") -> bool:
    """Add phone number or user_id to the opt-out registry."""
    init_db()
    now_iso = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO opt_out_registry (identifier, opt_out_time, reason)
            VALUES (?, ?, ?)
            ON CONFLICT(identifier) DO UPDATE SET
                opt_out_time = excluded.opt_out_time,
                reason = excluded.reason;
            """,
            (identifier, now_iso, reason),
        )
        conn.commit()
    logger.info(f"Registered opt-out for {identifier}")
    return True


def log_outbound_call(
    call_id: str,
    phone_number: str,
    patient_name: str,
    reminder_type: str = "Medication Follow-up",
    status: str = "initiated",
) -> dict[str, Any]:
    """Log a new outbound call in the database."""
    init_db()
    now_iso = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO outbound_calls (
                call_id, phone_number, patient_name, reminder_type, status, retry_count, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, 0, ?, ?);
            """,
            (call_id, phone_number, patient_name, reminder_type, status, now_iso, now_iso),
        )
        conn.commit()
    return {
        "call_id": call_id,
        "phone_number": phone_number,
        "patient_name": patient_name,
        "reminder_type": reminder_type,
        "status": status,
        "created_at": now_iso,
    }


def update_call_outcome(
    call_id: str,
    outcome: str,
    next_retry_iso: Optional[str] = None,
) -> bool:
    """Update call status and retry details based on outcome (e.g., completed, no_answer, busy, voicemail, immediate_hangup, opt_out)."""
    init_db()
    now_iso = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE outbound_calls
            SET status = ?,
                retry_count = retry_count + CASE WHEN ? IN ('no_answer', 'busy', 'immediate_hangup') THEN 1 ELSE 0 END,
                next_retry_at = ?,
                updated_at = ?
            WHERE call_id = ?;
            """,
            (outcome, outcome, next_retry_iso, now_iso, call_id),
        )
        conn.commit()
        return cursor.rowcount > 0

