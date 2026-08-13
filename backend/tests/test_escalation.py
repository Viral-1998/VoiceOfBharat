import sys
from pathlib import Path

# Add backend/src to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import db


def test_create_escalation_success():
    db.init_db()
    res = db.create_escalation_request(
        user_id="test_user_esc_1",
        caller_name="Ramesh",
        phone_number="+919876543210",
        reason="Red-flag Emergency Symptom",
        summary="Caller Ramesh reported severe chest pain for 30 minutes. Triage: RED Emergency. Location: Pune. Contact: +919876543210.",
        urgency="emergency",
        caller_language="English",
        preferred_followup="phone_call",
    )

    assert res["status"] == "open"
    assert res["id"].startswith("ESC-")
    assert res["urgency"] == "emergency"
    assert res["is_duplicate_updated"] is False

    # Check retrieval via get_escalation_requests
    all_requests = db.get_escalation_requests()
    req_ids = [r["id"] for r in all_requests]
    assert res["id"] in req_ids


def test_escalation_privacy_sanitization():
    db.init_db()
    sensitive_summary = "Caller OTP: 4920 and PIN: 1234, Aadhaar: 1234-5678-9012. Needs doctor for high fever."
    res = db.create_escalation_request(
        user_id="test_user_esc_privacy",
        caller_name="Privacy Tester",
        reason="Doctor Request",
        summary=sensitive_summary,
        urgency="high",
    )

    clean_summary = res["summary"]
    assert "4920" not in clean_summary
    assert "1234-5678-9012" not in clean_summary
    assert "[REDACTED]" in clean_summary or "[REDACTED_GOVT_ID]" in clean_summary


def test_escalation_duplicate_prevention():
    db.init_db()
    user_id = "test_user_dup_123"

    # First request
    res1 = db.create_escalation_request(
        user_id=user_id,
        caller_name="Suresh",
        phone_number="+919999900000",
        reason="Doctor Request",
        summary="Initial complaint: fever and cough.",
        urgency="medium",
    )
    first_id = res1["id"]
    assert res1["status"] == "open"

    # Second request from same user while first is open
    res2 = db.create_escalation_request(
        user_id=user_id,
        caller_name="Suresh",
        phone_number="+919999900000",
        reason="Doctor Request",
        summary="Follow up: severe shortness of breath.",
        urgency="emergency",
    )

    assert res2["id"] == first_id
    assert res2["is_duplicate_updated"] is True
    assert "fever and cough" in res2["summary"]
    assert "shortness of breath" in res2["summary"]
    assert res2["urgency"] == "emergency"


def test_update_escalation_status():
    db.init_db()
    res = db.create_escalation_request(
        user_id="test_user_status_change",
        caller_name="Pooja",
        reason="Red-flag Emergency Symptom",
        summary="Patient feels dizzy after fall.",
        urgency="high",
    )
    req_id = res["id"]

    # Mark as in_progress
    assert db.update_escalation_status(req_id, "in_progress") is True
    requests = db.get_escalation_requests("in_progress")
    in_prog_ids = [r["id"] for r in requests]
    assert req_id in in_prog_ids

    # Mark as resolved
    assert db.update_escalation_status(req_id, "resolved") is True
    requests_res = db.get_escalation_requests("resolved")
    res_ids = [r["id"] for r in requests_res]
    assert req_id in res_ids
