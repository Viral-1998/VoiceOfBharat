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
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS escalation_requests (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                caller_name TEXT NOT NULL,
                phone_number TEXT DEFAULT 'Not provided',
                reason TEXT NOT NULL,
                summary TEXT NOT NULL,
                urgency TEXT DEFAULT 'high',
                caller_language TEXT DEFAULT 'English',
                preferred_followup TEXT DEFAULT 'phone_call',
                status TEXT DEFAULT 'open',
                permission_granted INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS call_analytics (
                call_id TEXT PRIMARY KEY,
                channel TEXT DEFAULT 'browser',
                phone_number TEXT DEFAULT 'default_caller',
                start_time TEXT NOT NULL,
                end_time TEXT,
                duration_seconds INTEGER DEFAULT 0,
                status TEXT NOT NULL,
                failure_category TEXT DEFAULT 'none',
                outcome_summary TEXT DEFAULT '',
                triage_level TEXT DEFAULT 'none',
                escalation_created INTEGER DEFAULT 0,
                first_response_latency_ms REAL DEFAULT 0.0,
                created_at TEXT NOT NULL
            );
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS clinic_appointments (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                patient_name TEXT NOT NULL,
                facility_name TEXT NOT NULL,
                doctor_name TEXT NOT NULL,
                appointment_date TEXT NOT NULL,
                appointment_slot TEXT NOT NULL,
                status TEXT DEFAULT 'confirmed',
                created_at TEXT NOT NULL
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


def register_opt_out(
    identifier: str, reason: str = "User requested opt-out during call"
) -> bool:
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
            (
                call_id,
                phone_number,
                patient_name,
                reminder_type,
                status,
                now_iso,
                now_iso,
            ),
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


# =============================================================================
# HUMAN ESCALATION REQUEST HELPER FUNCTIONS (DAY 7)
# =============================================================================


def sanitize_summary(text: str) -> str:
    """Remove private/sensitive details (OTPs, PINs, bank accounts, Aadhaar) from summary text."""
    import re

    # Mask 12-digit Aadhaar / Account numbers
    text = re.sub(r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}\b", "[REDACTED_GOVT_ID]", text)
    # Mask 4-6 digit OTPs / PINs
    text = re.sub(
        r"\b(otp|pin|password|passcode)[:\s]*\d{4,6}\b",
        r"\1: [REDACTED]",
        text,
        flags=re.IGNORECASE,
    )
    # Mask card numbers (16 digits)
    text = re.sub(
        r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b", "[REDACTED_CARD]", text
    )
    return text


def create_escalation_request(
    user_id: str,
    reason: str,
    summary: str,
    caller_name: str = "Anonymous Caller",
    phone_number: str = "Not provided",
    urgency: str = "high",
    caller_language: str = "English",
    preferred_followup: str = "phone_call",
    permission_granted: bool = True,
) -> dict[str, Any]:
    """Create a new human escalation request or update an existing open request to prevent duplicates (DAY 7)."""
    import random

    init_db()
    clean_summary = sanitize_summary(summary)
    now_iso = datetime.now(timezone.utc).isoformat()
    valid_urgencies = {"low", "medium", "high", "emergency"}
    urgency_clean = urgency.lower() if urgency.lower() in valid_urgencies else "high"

    with get_connection() as conn:
        cursor = conn.cursor()

        # Check for duplicate open request from the same user_id or phone_number
        cursor.execute(
            """
            SELECT id, summary FROM escalation_requests
            WHERE (user_id = ? OR (phone_number != 'Not provided' AND phone_number = ?))
              AND status IN ('open', 'in_progress')
            ORDER BY created_at DESC LIMIT 1;
            """,
            (user_id, phone_number),
        )
        existing = cursor.fetchone()

        if existing:
            request_id = existing["id"]
            updated_summary = f"{existing['summary']} | Update: {clean_summary}"
            cursor.execute(
                """
                UPDATE escalation_requests
                SET summary = ?,
                    urgency = ?,
                    updated_at = ?
                WHERE id = ?;
                """,
                (updated_summary, urgency_clean, now_iso, request_id),
            )
            conn.commit()
            logger.info(
                f"Updated existing open escalation request {request_id} for user {user_id}"
            )
            return {
                "id": request_id,
                "user_id": user_id,
                "caller_name": caller_name,
                "phone_number": phone_number,
                "reason": reason,
                "summary": updated_summary,
                "urgency": urgency_clean,
                "caller_language": caller_language,
                "preferred_followup": preferred_followup,
                "status": "updated",
                "is_duplicate_updated": True,
                "created_at": now_iso,
            }

        # Generate a unique human-friendly Reference ID (e.g. ESC-8492)
        rand_num = random.randint(1000, 9999)
        request_id = f"ESC-{rand_num}"

        cursor.execute(
            """
            INSERT INTO escalation_requests (
                id, user_id, caller_name, phone_number, reason, summary, urgency,
                caller_language, preferred_followup, status, permission_granted, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'open', ?, ?, ?);
            """,
            (
                request_id,
                user_id,
                caller_name,
                phone_number,
                reason,
                clean_summary,
                urgency_clean,
                caller_language,
                preferred_followup,
                1 if permission_granted else 0,
                now_iso,
                now_iso,
            ),
        )
        conn.commit()

    logger.info(
        f"Created escalation request {request_id} for {caller_name} (Urgency: {urgency_clean})"
    )
    return {
        "id": request_id,
        "user_id": user_id,
        "caller_name": caller_name,
        "phone_number": phone_number,
        "reason": reason,
        "summary": clean_summary,
        "urgency": urgency_clean,
        "caller_language": caller_language,
        "preferred_followup": preferred_followup,
        "status": "open",
        "is_duplicate_updated": False,
        "created_at": now_iso,
    }


def get_escalation_requests(
    status_filter: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Retrieve all escalation requests for the human help dashboard."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        if status_filter:
            cursor.execute(
                "SELECT * FROM escalation_requests WHERE status = ? ORDER BY created_at DESC;",
                (status_filter,),
            )
        else:
            cursor.execute(
                "SELECT * FROM escalation_requests ORDER BY created_at DESC;"
            )

        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def update_escalation_status(request_id: str, status: str) -> bool:
    """Update status of an escalation request (open, in_progress, resolved)."""
    init_db()
    valid_statuses = {"open", "in_progress", "resolved"}
    if status not in valid_statuses:
        return False
    now_iso = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE escalation_requests SET status = ?, updated_at = ? WHERE id = ?;",
            (status, now_iso, request_id),
        )
        conn.commit()
        return cursor.rowcount > 0


# =============================================================================
# CALL ANALYTICS & METRICS FUNCTIONS (DAY 8)
# =============================================================================


def log_call_start(
    call_id: str,
    channel: str = "browser",
    phone_number: str = "default_caller",
) -> dict[str, Any]:
    """Record initial call connection in SQLite analytics table."""
    init_db()
    now_iso = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO call_analytics (
                call_id, channel, phone_number, start_time, status,
                failure_category, outcome_summary, created_at
            ) VALUES (?, ?, ?, ?, 'in_progress', 'none', 'Call connected', ?)
            ON CONFLICT(call_id) DO UPDATE SET
                channel = excluded.channel,
                phone_number = excluded.phone_number,
                start_time = excluded.start_time;
            """,
            (call_id, channel, phone_number, now_iso, now_iso),
        )
        conn.commit()
    logger.info(f"Logged call start: {call_id} ({channel})")
    return {"call_id": call_id, "channel": channel, "start_time": now_iso}


def log_call_end(
    call_id: str,
    status: str = "failed",
    failure_category: str = "user_hangup",
    outcome_summary: str = "Consultation incomplete",
    duration_seconds: int = 0,
    latency_ms: float = 0.0,
    triage_level: str = "none",
    escalation_created: int = 0,
) -> bool:
    """Record call outcome, duration, status (successful/failed), and metrics on call end."""
    init_db()
    now_iso = datetime.now(timezone.utc).isoformat()
    clean_summary = sanitize_summary(outcome_summary)
    valid_statuses = {"successful", "failed", "in_progress"}
    status_clean = status if status in valid_statuses else "failed"

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE call_analytics
            SET end_time = ?,
                duration_seconds = ?,
                status = ?,
                failure_category = ?,
                outcome_summary = ?,
                triage_level = ?,
                escalation_created = ?,
                first_response_latency_ms = ?
            WHERE call_id = ?;
            """,
            (
                now_iso,
                duration_seconds,
                status_clean,
                failure_category,
                clean_summary,
                triage_level,
                escalation_created,
                latency_ms,
                call_id,
            ),
        )
        conn.commit()
        updated = cursor.rowcount > 0

    if not updated:
        # Fallback insert if start wasn't logged explicitly
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO call_analytics (
                    call_id, channel, phone_number, start_time, end_time,
                    duration_seconds, status, failure_category, outcome_summary,
                    triage_level, escalation_created, first_response_latency_ms, created_at
                ) VALUES (?, 'browser', 'default_caller', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    call_id,
                    now_iso,
                    now_iso,
                    duration_seconds,
                    status_clean,
                    failure_category,
                    clean_summary,
                    triage_level,
                    escalation_created,
                    latency_ms,
                    now_iso,
                ),
            )
            conn.commit()

    logger.info(
        f"Logged call end for {call_id}: status={status_clean}, duration={duration_seconds}s, failure={failure_category}"
    )
    return True


def mark_call_success(
    call_id: str,
    outcome_summary: str,
    triage_level: str = "none",
    escalation_created: int = 0,
) -> bool:
    """Mark an active call as successful upon completing a key objective (triage, PHC lookup, escalation, opt-out, or consent save)."""
    init_db()
    clean_summary = sanitize_summary(outcome_summary)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE call_analytics
            SET status = 'successful',
                failure_category = 'none',
                outcome_summary = CASE
                    WHEN outcome_summary = 'Call connected' OR outcome_summary = 'Consultation incomplete' THEN ?
                    ELSE outcome_summary || ' | ' || ?
                END,
                triage_level = CASE WHEN ? != 'none' THEN ? ELSE triage_level END,
                escalation_created = CASE WHEN ? = 1 THEN 1 ELSE escalation_created END
            WHERE call_id = ?;
            """,
            (
                clean_summary,
                clean_summary,
                triage_level,
                triage_level,
                escalation_created,
                call_id,
            ),
        )
        conn.commit()
        return cursor.rowcount > 0


def get_analytics_summary(
    channel_filter: Optional[str] = None,
) -> dict[str, Any]:
    """Retrieve aggregated call analytics metrics for the Day 8 Dashboard."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()

        # Query total, successful, failed counts
        if channel_filter and channel_filter.lower() != "all":
            cursor.execute(
                """
                SELECT
                    COUNT(*) as total_calls,
                    SUM(CASE WHEN status = 'successful' THEN 1 ELSE 0 END) as successful_calls,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_calls,
                    AVG(CASE WHEN first_response_latency_ms > 0 THEN first_response_latency_ms ELSE NULL END) as avg_latency,
                    SUM(CASE WHEN escalation_created = 1 THEN 1 ELSE 0 END) as total_escalations
                FROM call_analytics
                WHERE channel = ?;
                """,
                (channel_filter.lower(),),
            )
        else:
            cursor.execute(
                """
                SELECT
                    COUNT(*) as total_calls,
                    SUM(CASE WHEN status = 'successful' THEN 1 ELSE 0 END) as successful_calls,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_calls,
                    AVG(CASE WHEN first_response_latency_ms > 0 THEN first_response_latency_ms ELSE NULL END) as avg_latency,
                    SUM(CASE WHEN escalation_created = 1 THEN 1 ELSE 0 END) as total_escalations
                FROM call_analytics;
                """
            )
        counts = cursor.fetchone()

        total_calls = counts["total_calls"] or 0
        successful_calls = counts["successful_calls"] or 0
        failed_calls = counts["failed_calls"] or 0
        avg_latency_ms = round(counts["avg_latency"] or 0.0, 1)
        total_escalations = counts["total_escalations"] or 0

        success_rate = (
            round((successful_calls / total_calls) * 100, 1) if total_calls > 0 else 0.0
        )

        # Failure categories breakdown
        cursor.execute(
            """
            SELECT failure_category, COUNT(*) as count
            FROM call_analytics
            WHERE status = 'failed' AND failure_category != 'none'
            GROUP BY failure_category;
            """
        )
        failure_rows = cursor.fetchall()
        failure_breakdown = {
            row["failure_category"]: row["count"] for row in failure_rows
        }

        # Fetch recent 20 call logs for call history table
        cursor.execute(
            """
            SELECT call_id, channel, phone_number, start_time, duration_seconds,
                   status, failure_category, outcome_summary, triage_level,
                   escalation_created, first_response_latency_ms, created_at
            FROM call_analytics
            ORDER BY created_at DESC
            LIMIT 20;
            """
        )
        recent_rows = cursor.fetchall()
        recent_calls = [dict(row) for row in recent_rows]

    return {
        "definition_of_success": (
            "A call is marked SUCCESSFUL when the caller receives safe health guidance, "
            "completes a symptom triage assessment, looks up health facilities, "
            "creates a human escalation request, or manages caller memory/opt-out preferences."
        ),
        "total_calls": total_calls,
        "successful_calls": successful_calls,
        "failed_calls": failed_calls,
        "success_rate_percent": success_rate,
        "avg_latency_ms": avg_latency_ms,
        "total_escalations": total_escalations,
        "failure_breakdown": failure_breakdown,
        "recent_calls": recent_calls,
    }


def log_simulated_call(
    status: str = "successful",
    failure_category: str = "none",
    outcome_summary: str = "Simulated triage assessment completed",
    channel: str = "browser",
    duration_seconds: int = 35,
    latency_ms: float = 430.0,
) -> dict[str, Any]:
    """Helper for testing success and failure paths on the Day 8 dashboard."""
    import random

    init_db()
    rand_id = f"TEST-CALL-{random.randint(1000, 9999)}"
    now_iso = datetime.now(timezone.utc).isoformat()

    log_call_start(rand_id, channel=channel, phone_number="test_caller")
    log_call_end(
        rand_id,
        status=status,
        failure_category=failure_category,
        outcome_summary=outcome_summary,
        duration_seconds=duration_seconds,
        latency_ms=latency_ms,
        triage_level="GREEN" if status == "successful" else "none",
        escalation_created=1 if "escalation" in outcome_summary.lower() else 0,
    )
    return {
        "call_id": rand_id,
        "status": status,
        "failure_category": failure_category,
        "outcome_summary": outcome_summary,
        "timestamp": now_iso,
    }


def create_appointment(
    user_id: str,
    patient_name: str,
    facility_name: str,
    doctor_name: str,
    appointment_date: str,
    appointment_slot: str,
) -> dict[str, Any]:
    """Create and persist a new clinic appointment in the database."""
    import random

    init_db()
    apt_id = f"APT-{random.randint(1000, 9999)}"
    now_iso = datetime.now(timezone.utc).isoformat()

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO clinic_appointments (id, user_id, patient_name, facility_name, doctor_name, appointment_date, appointment_slot, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'confirmed', ?)
            """,
            (
                apt_id,
                user_id,
                patient_name,
                facility_name,
                doctor_name,
                appointment_date,
                appointment_slot,
                now_iso,
            ),
        )
        conn.commit()

    return {
        "id": apt_id,
        "user_id": user_id,
        "patient_name": patient_name,
        "facility_name": facility_name,
        "doctor_name": doctor_name,
        "appointment_date": appointment_date,
        "appointment_slot": appointment_slot,
        "status": "confirmed",
        "created_at": now_iso,
    }


def get_appointments_for_user(user_id: str) -> list[dict[str, Any]]:
    """Retrieve active appointments for a user."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM clinic_appointments WHERE user_id = ? AND status = 'confirmed' ORDER BY created_at DESC",
            (user_id,),
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def cancel_appointment(appointment_id: str) -> bool:
    """Cancel a clinic appointment by ID."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE clinic_appointments SET status = 'cancelled' WHERE id = ?",
            (appointment_id,),
        )
        conn.commit()
        return cursor.rowcount > 0

