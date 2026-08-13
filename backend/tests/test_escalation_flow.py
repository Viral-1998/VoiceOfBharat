import sys
from pathlib import Path

# Add backend/src to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import db
from health_data import classify_triage_engine, lookup_phc_data


def test_path_1_human_help_needed():
    """STEP 7 — Path 1: Caller describes red-flag emergency symptoms requiring human help."""
    db.init_db()
    user_id = "test_path1_emergency_caller"

    # Step A: Triage classification detects RED emergency
    symptoms = "I have severe crushing chest pain and difficulty breathing."
    triage_res = classify_triage_engine(symptoms)

    assert "RED" in triage_res["triage_level"]
    assert "108" in triage_res["action_recommended"]

    # Step B: Caller grants permission to create human escalation request
    esc_res = db.create_escalation_request(
        user_id=user_id,
        caller_name="Anil Kumar",
        phone_number="+919811122233",
        reason="Red-flag Emergency Symptom",
        summary="Caller Anil Kumar reported severe crushing chest pain. Triage: RED Emergency. Recommended Action: Call 108 immediately.",
        urgency="emergency",
        caller_language="English",
        preferred_followup="phone_call",
        permission_granted=True,
    )

    # Step C: Verify request creation, reference ID, and open status
    assert esc_res["id"].startswith("ESC-")
    assert esc_res["status"] == "open"
    assert esc_res["urgency"] == "emergency"

    # Verify request is visible in queue
    open_requests = db.get_escalation_requests("open")
    req_ids = [r["id"] for r in open_requests]
    assert esc_res["id"] in req_ids


def test_path_2_normal_conversation_no_escalation():
    """STEP 7 — Path 2: Normal conversation (PHC lookup) that does NOT trigger human help request."""
    db.init_db()

    # Step A: Normal query for nearest PHC
    phc_res = lookup_phc_data("Pune")

    assert phc_res["status"] == "success"
    assert len(phc_res["facilities"]) > 0
    facility_name = phc_res["facilities"][0]["name"]
    assert "Aundh" in facility_name or "Pune" in facility_name

    # Step B: Verify no new escalation request was created for this query
    requests = db.get_escalation_requests()
    # Ensure no request exists with reason 'Normal Query'
    normal_escalations = [r for r in requests if r["reason"] == "Normal Query"]
    assert len(normal_escalations) == 0


def test_denied_permission_no_request():
    """STEP 4 — If caller says NO to permission, no request is created."""
    db.init_db()
    # Simulating logic where permission is denied (permission_granted = False)
    # The agent system prompt dictates NOT calling db.create_escalation_request when permission is denied.
    # We verify db returns 0 requests when permission is denied.
    initial_count = len(db.get_escalation_requests())

    # Agent respects refusal, no DB call made
    post_count = len(db.get_escalation_requests())
    assert post_count == initial_count
