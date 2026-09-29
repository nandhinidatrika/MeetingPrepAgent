"""Tests for SQLite database operations and schemas."""
import os
import tempfile
import pytest
from app.config import get_settings
from app.database import db


@pytest.fixture(autouse=True)
def test_db_setup(monkeypatch):
    """Use a temporary database file for all tests."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        temp_db_path = tmp.name

    settings = get_settings()
    monkeypatch.setattr(settings, "sqlite_db_path", temp_db_path)
    db.init_db()

    yield temp_db_path

    # Cleanup
    if os.path.exists(temp_db_path):
        try:
            os.remove(temp_db_path)
        except Exception:
            pass


def test_client_crud():
    """Test creating, reading, updating, and deleting client entities."""
    client = db.create_client(
        name="Sarah Chen",
        organization="ABC Technologies",
        email="sarah@abctech.io",
        role="VP of Engineering",
        notes="Primary sponsor.",
    )
    assert client.id is not None
    assert client.name == "Sarah Chen"
    assert client.organization == "ABC Technologies"

    # Fetch by ID
    fetched = db.get_client_by_id(client.id)
    assert fetched is not None
    assert fetched.name == "Sarah Chen"

    # Fetch by Name
    by_name = db.get_client_by_name("sarah chen")
    assert by_name is not None
    assert by_name.id == client.id

    # Update
    updated = db.update_client(client.id, role="Chief Technology Officer")
    assert updated is not None
    assert updated.role == "Chief Technology Officer"

    # Delete
    db.delete_client(client.id)
    assert db.get_client_by_id(client.id) is None


def test_meeting_crud():
    """Test creating, reading, updating, and deleting meeting records."""
    client = db.create_client(name="Alex Rivera", organization="Acme Corp")
    meeting = db.create_meeting(
        client_id=client.id,
        title="Sprint Planning Meeting",
        meeting_date="2026-10-15",
        meeting_time="02:00 PM",
        topic="Q4 Roadmap Review",
        status="upcoming",
    )
    assert meeting.id is not None
    assert meeting.client_id == client.id
    assert meeting.title == "Sprint Planning Meeting"

    # Get meetings by client
    meetings = db.get_meetings_by_client(client.id)
    assert len(meetings) == 1
    assert meetings[0].id == meeting.id

    # Update meeting
    updated = db.update_meeting(
        meeting.id,
        status="prepared",
        brief_cache="# Briefing Content",
    )
    assert updated is not None
    assert updated.status == "prepared"
    assert updated.brief_cache == "# Briefing Content"


def test_follow_up_crud():
    """Test creating, updating, and querying follow-up action items."""
    client = db.create_client(name="Taylor Smith")
    meeting = db.create_meeting(
        client_id=client.id,
        title="Architecture Discussion",
        meeting_date="2026-10-20",
    )

    fu = db.create_follow_up(
        meeting_id=meeting.id,
        client_id=client.id,
        task="Send revised security architecture diagram",
        due_date="2026-10-25",
    )
    assert fu.id is not None
    assert fu.status == "pending"

    pending = db.get_pending_follow_ups()
    assert len(pending) == 1
    assert pending[0].id == fu.id

    # Toggle to completed
    db.toggle_follow_up_status(fu.id, completed=True)
    pending_after = db.get_pending_follow_ups()
    assert len(pending_after) == 0


def test_action_logs():
    """Test action logging audit trail."""
    log = db.log_action(
        action_type="retain",
        summary="Retained 5 memory units in Hindsight Cloud",
    )
    assert log.id is not None
    assert log.action_type == "retain"

    recent = db.get_recent_actions(limit=5)
    assert len(recent) >= 1
    assert recent[0].summary == "Retained 5 memory units in Hindsight Cloud"
