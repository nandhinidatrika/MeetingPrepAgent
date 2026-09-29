"""Tests for Pydantic models and data serialization."""
from app.models.schemas import (
    Client,
    ExtractedNoteItems,
    FollowUp,
    Meeting,
    MeetingBrief,
    MemoryPayload,
    RecalledMemoryItem,
)
from app.utils.helpers import build_memory_chunks, format_brief_markdown


def test_extracted_note_items_schema():
    """Test ExtractedNoteItems model defaults and validation."""
    items = ExtractedNoteItems(
        decisions=["Launch dashboard by Oct 15"],
        commitments=["Write API documentation"],
        deadlines=["Oct 15, 2026"],
        preferences=["Prefers bulleted updates"],
        requirements=["Multi-tenant support"],
        follow_ups=["Follow up with DevOps"],
        unresolved_issues=["Auth blocker with Okta"],
    )
    assert len(items.decisions) == 1
    assert len(items.unresolved_issues) == 1
    data = items.model_dump()
    assert data["decisions"][0] == "Launch dashboard by Oct 15"


def test_memory_payload_and_chunking():
    """Test building structured semantic memory chunks for Hindsight retention."""
    payload = MemoryPayload(
        client_id="client-123",
        client_name="Sarah Chen",
        organization="ABC Technologies",
        meeting_id="m-456",
        meeting_title="Sprint 1 Review",
        meeting_date="2026-09-15",
        topic="Dashboard Analytics",
        items=ExtractedNoteItems(
            decisions=["Approved regional filtering"],
            commitments=["Send updates twice per week"],
            deadlines=["Release: Oct 25"],
            preferences=["Concise updates"],
            requirements=["Okta SSO"],
            unresolved_issues=["Security review pending"],
        ),
        raw_notes="Raw meeting text transcript...",
    )

    chunks = build_memory_chunks(payload)
    assert len(chunks) >= 6  # decisions, commitments, deadlines, preferences, requirements, unresolved, summary

    # Verify tags and content in chunks
    decision_chunk = next(c for c in chunks if "type:decision" in c["tags"])
    assert "Approved regional filtering" in decision_chunk["content"]
    assert "client:sarah_chen" in decision_chunk["tags"]
    assert "org:abc_technologies" in decision_chunk["tags"]


def test_meeting_brief_formatting():
    """Test formatting MeetingBrief into markdown."""
    brief = MeetingBrief(
        client_name="Sarah Chen",
        meeting_title="Meeting 3: Final Pre-Launch Review",
        meeting_date="2026-10-01",
        objective="Finalize launch readiness and resolve auth blocker.",
        previous_discussions="Discussed dashboard requirements and shifted API deadline.",
        key_decisions=["Build analytics dashboard", "Add regional filtering"],
        outstanding_commitments=["Deliver API documentation"],
        deadlines=["Dashboard Launch: Oct 15", "API Docs: Oct 25"],
        client_preferences=["Concise updates", "Twice weekly syncs"],
        unresolved_issues=["Enterprise Okta SSO blocker"],
        what_changed_since_last_meeting="API doc deadline shifted from Oct 15 to Oct 25.",
        memory_sources_count=8,
    )

    md = format_brief_markdown(brief)
    assert "📋 AI Meeting Brief: Meeting 3: Final Pre-Launch Review" in md
    assert "Sarah Chen" in md
    assert "🎯 Meeting Objective" in md
    assert "🔄 What Changed Since Last Meeting" in md
    assert "Enterprise Okta SSO blocker" in md
