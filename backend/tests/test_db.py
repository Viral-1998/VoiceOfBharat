from pathlib import Path

import pytest

import db


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path: Path):
    test_db_path = tmp_path / "test_memory.db"
    db.DB_DIR = tmp_path
    db.DB_PATH = test_db_path
    db.init_db()
    yield


def test_init_and_get_empty():
    caller = db.get_caller("user_999")
    assert caller is None


def test_save_and_get_caller():
    saved = db.save_caller(
        user_id="user_123",
        name="Ramesh",
        language_preference="Hinglish",
        facts={
            "age_band": "40-50",
            "ongoing_conditions": "Mild hypertension",
            "last_triage_outcome": "Advised warm fluids and PHC visit if fever persists",
        },
    )

    assert saved["user_id"] == "user_123"
    assert saved["name"] == "Ramesh"

    retrieved = db.get_caller("user_123")
    assert retrieved is not None
    assert retrieved["name"] == "Ramesh"
    assert retrieved["language_preference"] == "Hinglish"
    assert retrieved["facts"]["age_band"] == "40-50"
    assert retrieved["facts"]["ongoing_conditions"] == "Mild hypertension"


def test_update_caller_facts():
    db.save_caller("user_123", "Ramesh", "English", {"age_band": "40-50"})
    db.save_caller(
        "user_123",
        "Ramesh Kumar",
        "Hindi",
        {"age_band": "40-50", "ongoing_conditions": "Recovered from fever"},
    )

    retrieved = db.get_caller("user_123")
    assert retrieved["name"] == "Ramesh Kumar"
    assert retrieved["language_preference"] == "Hindi"
    assert retrieved["facts"]["ongoing_conditions"] == "Recovered from fever"


def test_delete_caller():
    db.save_caller("user_123", "Ramesh", "English", {})
    assert db.get_caller("user_123") is not None

    deleted = db.delete_caller("user_123")
    assert deleted is True
    assert db.get_caller("user_123") is None

    # Delete non-existent
    assert db.delete_caller("user_123") is False
