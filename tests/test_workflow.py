"""Integration tests for the complete Meeting Prep Agent workflow."""
import os
import tempfile
import pytest

from app.config import get_settings
from app.database import db
from app.models.schemas import ExtractedNoteItems
from app.services.meeting_service import MeetingService


@pytest.fixture(autouse=True)
def isolated_env(monkeypatch):
    """Set up temporary database for integration tests."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        temp_db_path = tmp.name

    settings = get_settings()
    monkeypatch.setattr(settings, "sqlite_db_path", temp_db_path)
    db.init_db()

    yield

    if os.path.exists(temp_db_path):
        try:
            os.remove(temp_db_path)
        except Exception:
            pass


def test_seed_demo_scenario_workflow():
    """Test seeding the 3-meeting ABC Technologies demo scenario."""
    service = MeetingService()
    # Seed without live Hindsight calls during unit test
    result = service.seed_demo_scenario(retain_to_hindsight=False)

    assert result["client"].name == "Sarah Chen"
    assert len(result["meetings"]) == 3

    # Check database state
    clients = db.get_all_clients()
    assert len(clients) == 1
    assert clients[0].name == "Sarah Chen"

    meetings = db.get_meetings_by_client(clients[0].id)
    assert len(meetings) == 3

    # Verify meeting 1 is completed
    m1 = next(m for m in meetings if "Meeting 1" in m.title)
    assert m1.status == "completed"
    assert "analytics dashboard" in m1.notes.lower()

    # Verify meeting 2 is completed
    m2 = next(m for m in meetings if "Meeting 2" in m.title)
    assert m2.status == "completed"
    assert "regional filtering" in m2.notes.lower()

    # Verify meeting 3 is upcoming
    m3 = next(m for m in meetings if "Meeting 3" in m.title)
    assert m3.status == "upcoming"


def test_save_and_remember_post_meeting_flow():
    """Test saving post-meeting notes and updating database metadata."""
    service = MeetingService()
    client = db.create_client(name="Alex Rivera", organization="Acme Corp")
    meeting = db.create_meeting(
        client_id=client.id,
        title="Q4 Kickoff",
        meeting_date="2026-10-01",
        status="upcoming",
    )

    items = ExtractedNoteItems(
        decisions=["Adopt new architecture"],
        commitments=["Deliver draft specifications"],
        deadlines=["Nov 15, 2026"],
        preferences=["Weekly email updates"],
        requirements=["SOC2 compliance"],
        follow_ups=["Send SOC2 report to Alex"],
        unresolved_issues=["Budget signoff pending"],
    )

    ok, msg, chunks = service.save_and_remember_post_meeting(
        client_id=client.id,
        meeting_id=meeting.id,
        raw_notes="Met with Alex. Agreed on new architecture. Need SOC2 report.",
        extracted_items=items,
        retain_to_hindsight=False,
    )

    assert ok is True

    # Verify meeting status is updated in DB
    updated_m = db.get_meeting_by_id(meeting.id)
    assert updated_m.status == "completed"
    assert "Agreed on new architecture" in updated_m.notes

    # Verify follow-up task is created
    follow_ups = db.get_pending_follow_ups(client_id=client.id)
    assert len(follow_ups) >= 1
    assert "Deliver draft specifications" in [f.task for f in follow_ups]
