"""Tests for GroqService and HindsightService."""
import pytest
from app.config import get_settings
from app.models.schemas import ExtractedNoteItems, MemoryPayload, RecalledMemoryItem
from app.services.groq_service import GroqService
from app.services.hindsight_service import HindsightService


def test_hindsight_service_unconfigured_graceful(monkeypatch):
    """Verify Hindsight service fails gracefully without crashing when credentials are not yet set."""
    settings = get_settings()
    monkeypatch.setattr(settings, "hindsight_api_key", "")
    service = HindsightService()
    service._client = None
    
    payload = MemoryPayload(
        client_id="c1",
        client_name="Test User",
        meeting_id="m1",
        meeting_title="Kickoff",
        meeting_date="2026-09-01",
        topic="Testing",
        items=ExtractedNoteItems(decisions=["Test decision"]),
    )

    ok, msg, chunks = service.retain_meeting_memory(payload)
    # Should report not configured without exception
    assert ok is False
    assert len(chunks) == 0

    recalled = service.recall_memories(query="test query", client_name="Test User")
    assert isinstance(recalled, list)
    assert len(recalled) == 0


def test_groq_service_unconfigured_graceful(monkeypatch):
    """Verify Groq service fails gracefully when credentials are not yet set."""
    settings = get_settings()
    monkeypatch.setattr(settings, "groq_api_key", "")
    service = GroqService()
    service._client = None

    ok, msg, extracted = service.extract_structured_notes(
        raw_notes="Some test notes",
        client_name="Test User",
    )
    assert ok is False
    assert isinstance(extracted, ExtractedNoteItems)

    ok_b, msg_b, brief = service.generate_meeting_brief(
        client_name="Test User",
        organization="Test Org",
        meeting_title="Strategy Sync",
        meeting_date="2026-10-01",
        meeting_topic="Roadmap",
        recalled_memories=[],
    )
    assert ok_b is False
    assert brief is not None
    assert brief.client_name == "Test User"
