import sys
from pathlib import Path

# Add backend/src to sys.path for importing modules under test
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import db
from health_data import classify_triage_engine, lookup_phc_data


def test_lookup_phc_success():
    res = lookup_phc_data("Pune")
    assert res["status"] == "success"
    assert "facilities" in res
    assert len(res["facilities"]) > 0
    assert "Aundh" in res["facilities"][0]["name"]
    assert "timestamp" in res
    assert "2026" in res["timestamp"]


def test_lookup_phc_pincode_match():
    res = lookup_phc_data("411007")
    assert res["status"] == "success"
    assert len(res["facilities"]) > 0
    assert res["facilities"][0]["district"] == "Pune"


def test_lookup_phc_failure_path():
    res = lookup_phc_data("Pune", simulate_offline=True)
    assert res["status"] == "error"
    assert res["error_type"] == "PORTAL_TIMEOUT"
    assert "108" in res["message"]
    assert "SPOKEN INSTRUCTION" in res["message"]


def test_classify_triage_emergency():
    res = classify_triage_engine("Severe chest pain and difficulty breathing")
    assert res["status"] == "success"
    assert "RED" in res["triage_level"]
    assert "108" in res["action_recommended"]


def test_classify_triage_urgent():
    res = classify_triage_engine(
        "High fever for 4 days and stomach pain", duration_days=4
    )
    assert res["status"] == "success"
    assert "YELLOW" in res["triage_level"]
    assert "Primary Health Centre" in res["action_recommended"]


def test_classify_triage_mild():
    res = classify_triage_engine("Slight runny nose and mild fatigue", duration_days=1)
    assert res["status"] == "success"
    assert "GREEN" in res["triage_level"]
    assert "Home Monitoring" in res["urgency_window"]


def test_memory_and_facility_chaining():
    db.init_db()
    # Save profile with district Jaipur
    db.save_caller(
        user_id="test_chaining_user",
        name="Sunita",
        language_preference="English",
        facts={"district": "Jaipur", "ongoing_conditions": "Fever"},
    )

    caller = db.get_caller("test_chaining_user")
    assert caller is not None
    assert caller["facts"]["district"] == "Jaipur"

    # Tool chaining lookup using saved district
    phc_res = lookup_phc_data(caller["facts"]["district"])
    assert phc_res["status"] == "success"
    assert phc_res["facilities"][0]["district"] == "Jaipur"
