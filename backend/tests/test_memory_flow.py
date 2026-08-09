import db


def test_full_day4_memory_and_privacy_flow(tmp_path):
    # Use temporary test database
    db.DB_DIR = tmp_path
    db.DB_PATH = tmp_path / "agent_memory.db"
    db.init_db()

    user_id = "caller_ramesh_101"

    # --- CALL 1: First Call (Unknown caller) ---
    assert db.get_caller(user_id) is None

    # Save caller after consent
    save_result = db.save_caller(
        user_id=user_id,
        name="Ramesh",
        language_preference="Hinglish",
        facts={
            "age_band": "35-40",
            "ongoing_conditions": "Mild fever and sore throat",
            "last_triage_outcome": "Advised warm saline gargles, hydration, and visiting PHC if fever exceeds 101F",
        },
    )

    assert save_result["user_id"] == user_id
    assert save_result["name"] == "Ramesh"

    # --- VERIFY STORAGE IN SQLITE ---
    retrieved = db.get_caller(user_id)
    assert retrieved is not None
    assert retrieved["name"] == "Ramesh"
    assert retrieved["language_preference"] == "Hinglish"
    assert retrieved["facts"]["ongoing_conditions"] == "Mild fever and sore throat"

    # --- CALL 2: Returning Call (Known caller recognized by ID) ---
    caller_profile = db.get_caller(user_id)
    assert caller_profile is not None

    name = caller_profile["name"]
    last_outcome = caller_profile["facts"].get("last_triage_outcome")

    personalized_greeting = (
        f"Namaste {name}, welcome back to Arogya Seva! Last time we spoke about {last_outcome}. "
        f"How are you feeling today?"
    )

    assert "Ramesh" in personalized_greeting
    assert "warm saline gargles" in personalized_greeting

    # --- FORGET ME TOOL (Wipe Record) ---
    deleted = db.delete_caller(user_id)
    assert deleted is True
    assert db.get_caller(user_id) is None
