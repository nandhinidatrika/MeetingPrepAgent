"""Helper utilities for formatting, parsing, and data manipulation."""
import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from app.models.schemas import ExtractedNoteItems, MeetingBrief, MemoryPayload, RecalledMemoryItem


def clean_json_string(raw_text: str) -> str:
    """Strip markdown backticks, codeblock identifiers, or trailing whitespace from JSON strings."""
    text = raw_text.strip()
    # Remove markdown code fences like ```json ... ```
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def parse_json_safely(raw_text: str, default: Any = None) -> Any:
    """Parse JSON safely with cleanup and fallback."""
    cleaned = clean_json_string(raw_text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Try finding the first '{' and last '}'
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(cleaned[start : end + 1])
            except json.JSONDecodeError:
                pass
        return default if default is not None else {}


def format_date_human(date_str: str) -> str:
    """Format ISO or YYYY-MM-DD date into a readable string like 'Oct 15, 2026'."""
    if not date_str:
        return "Not specified"
    try:
        if "T" in date_str:
            dt = datetime.fromisoformat(date_str)
        else:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%b %d, %Y")
    except Exception:
        return date_str


def build_memory_chunks(payload: MemoryPayload) -> List[Dict[str, Any]]:
    """
    Decompose a meeting's notes into high-signal structured memory chunks.
    Each chunk is enriched with client, meeting, and semantic tags for precise Hindsight retrieval.
    """
    chunks: List[Dict[str, Any]] = []
    base_tags = [
        f"client:{payload.client_name.lower().replace(' ', '_')}",
        f"meeting:{payload.meeting_id}",
    ]
    if payload.organization:
        base_tags.append(f"org:{payload.organization.lower().replace(' ', '_')}")

    # 1. Decisions
    for decision in payload.items.decisions:
        chunks.append({
            "content": f"Decision made with {payload.client_name} on {payload.meeting_date} regarding '{payload.topic}': {decision}",
            "context": f"Meeting: {payload.meeting_title} ({payload.meeting_date})",
            "tags": base_tags + ["type:decision", "category:governance"],
        })

    # 2. Commitments
    for commitment in payload.items.commitments:
        chunks.append({
            "content": f"Commitment established with {payload.client_name} on {payload.meeting_date}: {commitment}",
            "context": f"Meeting: {payload.meeting_title} ({payload.meeting_date})",
            "tags": base_tags + ["type:commitment", "category:action_item"],
        })

    # 3. Deadlines
    for deadline in payload.items.deadlines:
        chunks.append({
            "content": f"Deadline scheduled with {payload.client_name} during {payload.meeting_title}: {deadline}",
            "context": f"Meeting: {payload.meeting_title} ({payload.meeting_date})",
            "tags": base_tags + ["type:deadline", "category:milestone"],
        })

    # 4. Preferences
    for preference in payload.items.preferences:
        chunks.append({
            "content": f"Working / communication preference noted for {payload.client_name}: {preference}",
            "context": f"Observed during meeting on {payload.meeting_date}",
            "tags": base_tags + ["type:preference", "category:relationship"],
        })

    # 5. Requirements
    for req in payload.items.requirements:
        chunks.append({
            "content": f"Requirement specified by {payload.client_name} on {payload.meeting_date}: {req}",
            "context": f"Topic: {payload.topic}",
            "tags": base_tags + ["type:requirement", "category:technical"],
        })

    # 6. Unresolved Issues
    for issue in payload.items.unresolved_issues:
        chunks.append({
            "content": f"Unresolved issue / blocker with {payload.client_name} recorded on {payload.meeting_date}: {issue}",
            "context": f"Meeting: {payload.meeting_title}",
            "tags": base_tags + ["type:unresolved", "category:risk"],
        })

    # 7. Comprehensive synthesis chunk
    if payload.raw_notes:
        chunks.append({
            "content": f"Meeting Summary for {payload.client_name} on {payload.meeting_date} (Topic: {payload.topic}): {payload.raw_notes[:1000]}",
            "context": f"Full notes from {payload.meeting_title}",
            "tags": base_tags + ["type:meeting_summary", "category:overview"],
        })

    return chunks


def format_brief_markdown(brief: MeetingBrief) -> str:
    """Format a structured MeetingBrief into an executive Markdown briefing document."""
    md_lines = [
        f"# 📋 AI Meeting Brief: {brief.meeting_title}",
        f"**Client:** {brief.client_name} | **Date:** {brief.meeting_date} | **Memory Sources:** {brief.memory_sources_count} recalled items",
        "",
        "---",
        "",
        "### 🎯 Meeting Objective",
        brief.objective or "Not specified",
        "",
    ]

    if brief.what_changed_since_last_meeting:
        md_lines.extend([
            "### 🔄 What Changed Since Last Meeting",
            brief.what_changed_since_last_meeting,
            "",
        ])

    if brief.previous_discussions:
        md_lines.extend([
            "### 📜 Historical Context & Previous Discussions",
            brief.previous_discussions,
            "",
        ])

    if brief.key_decisions:
        md_lines.append("### ⚖️ Key Decisions Established")
        for item in brief.key_decisions:
            md_lines.append(f"- {item}")
        md_lines.append("")

    if brief.outstanding_commitments:
        md_lines.append("### 🤝 Outstanding Commitments")
        for item in brief.outstanding_commitments:
            md_lines.append(f"- {item}")
        md_lines.append("")

    if brief.deadlines:
        md_lines.append("### ⏰ Target Deadlines & Milestones")
        for item in brief.deadlines:
            md_lines.append(f"- {item}")
        md_lines.append("")

    if brief.client_preferences:
        md_lines.append("### 💡 Client Preferences & Working Style")
        for item in brief.client_preferences:
            md_lines.append(f"- {item}")
        md_lines.append("")

    if brief.unresolved_issues:
        md_lines.append("### ⚠️ Unresolved Issues & Blockers")
        for item in brief.unresolved_issues:
            md_lines.append(f"- {item}")
        md_lines.append("")

    if brief.recommended_talking_points:
        md_lines.append("### 💬 Recommended Talking Points")
        for item in brief.recommended_talking_points:
            md_lines.append(f"- {item}")
        md_lines.append("")

    if brief.suggested_questions:
        md_lines.append("### ❓ Suggested Questions to Ask")
        for item in brief.suggested_questions:
            md_lines.append(f"- {item}")
        md_lines.append("")

    if brief.risks_or_watchouts:
        md_lines.append("### 🛡️ Risks & Things to Watch")
        for item in brief.risks_or_watchouts:
            md_lines.append(f"- {item}")
        md_lines.append("")

    return "\n".join(md_lines)
