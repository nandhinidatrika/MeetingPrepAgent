"""Tests for prompt utilities, JSON sanitization, and helper functions."""
from app.models.schemas import MeetingBrief
from app.utils.helpers import clean_json_string, format_brief_markdown, format_date_human, parse_json_safely


def test_clean_json_string():
    """Test cleaning markdown-wrapped JSON responses from LLMs."""
    raw = "```json\n{\"key\": \"value\"}\n```"
    assert clean_json_string(raw) == "{\"key\": \"value\"}"

    raw_no_lang = "```\n{\"key\": \"value\"}\n```"
    assert clean_json_string(raw_no_lang) == "{\"key\": \"value\"}"

    plain = "{\"key\": \"value\"}"
    assert clean_json_string(plain) == "{\"key\": \"value\"}"


def test_parse_json_safely():
    """Test resilient JSON parsing with markdown codeblocks and messy text."""
    # Standard valid
    assert parse_json_safely('{"status": "ok"}') == {"status": "ok"}

    # Markdown block
    assert parse_json_safely('```json\n{"score": 95}\n```') == {"score": 95}

    # Embedded in conversational filler
    filler = 'Here is your json output:\n{"decisions": ["Approved"]}\nHope this helps!'
    parsed = parse_json_safely(filler)
    assert parsed == {"decisions": ["Approved"]}

    # Invalid fallback
    assert parse_json_safely("Invalid JSON String", default={"fallback": True}) == {"fallback": True}


def test_format_date_human():
    """Test human-friendly date string formatting."""
    assert format_date_human("2026-10-15") == "Oct 15, 2026"
    assert format_date_human("") == "Not specified"
    assert format_date_human("2026-09-01T10:00:00") == "Sep 01, 2026"


def test_format_brief_markdown_completeness():
    """Verify that all briefing sections are rendered in markdown."""
    brief = MeetingBrief(
        client_name="Sarah Chen",
        meeting_title="Sprint 3 Prep",
        meeting_date="2026-10-01",
        objective="Verify SSO fix",
        previous_discussions="Discussed dashboard features",
        key_decisions=["Decided on Okta"],
        outstanding_commitments=["Commitment A"],
        deadlines=["Oct 25"],
        client_preferences=["Concise updates"],
        unresolved_issues=["SSO blocker"],
        suggested_questions=["When will IT approve?"],
        risks_or_watchouts=["Security review delay"],
        recommended_talking_points=["Point 1", "Point 2"],
        what_changed_since_last_meeting="Timeline moved 2 weeks",
        memory_sources_count=5,
    )

    md = format_brief_markdown(brief)
    assert "### 🎯 Meeting Objective" in md
    assert "### 🔄 What Changed Since Last Meeting" in md
    assert "### ⚖️ Key Decisions Established" in md
    assert "### 🤝 Outstanding Commitments" in md
    assert "### ⏰ Target Deadlines & Milestones" in md
    assert "### 💡 Client Preferences & Working Style" in md
    assert "### ⚠️ Unresolved Issues & Blockers" in md
    assert "### 💬 Recommended Talking Points" in md
    assert "### ❓ Suggested Questions to Ask" in md
    assert "### 🛡️ Risks & Things to Watch" in md
