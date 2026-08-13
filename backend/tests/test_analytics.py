from pathlib import Path

import pytest

import db


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path: Path):
    test_db_path = tmp_path / "test_analytics.db"
    db.DB_DIR = tmp_path
    db.DB_PATH = test_db_path
    db.init_db()
    yield


def test_init_analytics_empty():
    summary = db.get_analytics_summary()
    assert summary["total_calls"] == 0
    assert summary["successful_calls"] == 0
    assert summary["failed_calls"] == 0
    assert summary["success_rate_percent"] == 0.0
    assert len(summary["recent_calls"]) == 0


def test_log_call_start_and_successful_end():
    call_id = "CALL-TEST-001"
    db.log_call_start(call_id, channel="browser", phone_number="user_888")

    # Mark call successful when triage tool fires
    db.mark_call_success(
        call_id,
        outcome_summary="Symptom triage completed (GREEN)",
        triage_level="GREEN",
    )

    # Finalize call end
    db.log_call_end(
        call_id=call_id,
        status="successful",
        failure_category="none",
        outcome_summary="Symptom triage completed (GREEN)",
        duration_seconds=30,
        latency_ms=410.5,
        triage_level="GREEN",
    )

    summary = db.get_analytics_summary()
    assert summary["total_calls"] == 1
    assert summary["successful_calls"] == 1
    assert summary["failed_calls"] == 0
    assert summary["success_rate_percent"] == 100.0
    assert summary["recent_calls"][0]["call_id"] == call_id
    assert summary["recent_calls"][0]["status"] == "successful"


def test_failed_call_logging():
    call_id = "CALL-TEST-002"
    db.log_call_start(call_id, channel="sip_outbound", phone_number="+919876543210")
    db.log_call_end(
        call_id=call_id,
        status="failed",
        failure_category="user_hangup",
        outcome_summary="Caller disconnected immediately (< 5s)",
        duration_seconds=4,
        latency_ms=0.0,
    )

    summary = db.get_analytics_summary()
    assert summary["total_calls"] == 1
    assert summary["successful_calls"] == 0
    assert summary["failed_calls"] == 1
    assert summary["success_rate_percent"] == 0.0
    assert summary["failure_breakdown"].get("user_hangup") == 1


def test_simulated_calls_increment_metrics():
    # Simulate 2 successful calls and 1 failed call
    db.log_simulated_call(status="successful", outcome_summary="Test Triage 1")
    db.log_simulated_call(status="successful", outcome_summary="Test PHC Lookup 2")
    db.log_simulated_call(
        status="failed",
        failure_category="incomplete_task",
        outcome_summary="Test Hangup 3",
    )

    summary = db.get_analytics_summary()
    assert summary["total_calls"] == 3
    assert summary["successful_calls"] == 2
    assert summary["failed_calls"] == 1
    assert summary["success_rate_percent"] == 66.7
    assert len(summary["recent_calls"]) == 3


def test_privacy_sanitization_in_analytics():
    raw = "User provided Aadhaar 1234 5678 9012 and OTP: 987654 for verification."
    clean = db.sanitize_summary(raw)
    assert "1234 5678 9012" not in clean
    assert "[REDACTED_GOVT_ID]" in clean
    assert "987654" not in clean
    assert "[REDACTED]" in clean
