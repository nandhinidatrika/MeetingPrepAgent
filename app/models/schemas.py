"""Pydantic data schemas for Meeting Prep Agent."""
from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, Field


class Client(BaseModel):
    """Client / Contact entity schema."""
    id: str
    name: str
    organization: str = ""
    email: str = ""
    role: str = ""
    notes: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class Meeting(BaseModel):
    """Meeting metadata schema."""
    id: str
    client_id: str
    title: str
    meeting_date: str
    meeting_time: str = "10:00 AM"
    status: str = "upcoming"  # upcoming, prepared, completed
    topic: str = ""
    notes: str = ""
    raw_transcript: str = ""
    brief_cache: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class FollowUp(BaseModel):
    """Follow-up action item schema."""
    id: str
    meeting_id: str
    client_id: str
    task: str
    owner: str = "Me"
    due_date: str = ""
    status: str = "pending"  # pending, completed
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class ActionLog(BaseModel):
    """System activity log entry."""
    id: str
    client_id: str = ""
    meeting_id: str = ""
    action_type: str  # retain, recall, prepare, reflect
    summary: str
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class ExtractedNoteItems(BaseModel):
    """Structured categories extracted from meeting notes."""
    decisions: List[str] = Field(default_factory=list)
    commitments: List[str] = Field(default_factory=list)
    deadlines: List[str] = Field(default_factory=list)
    preferences: List[str] = Field(default_factory=list)
    requirements: List[str] = Field(default_factory=list)
    follow_ups: List[str] = Field(default_factory=list)
    unresolved_issues: List[str] = Field(default_factory=list)


class MemoryPayload(BaseModel):
    """Structured payload sent for Hindsight retention."""
    client_id: str
    client_name: str
    organization: str = ""
    meeting_id: str
    meeting_title: str
    meeting_date: str
    topic: str = ""
    items: ExtractedNoteItems = Field(default_factory=ExtractedNoteItems)
    raw_notes: str = ""


class RecalledMemoryItem(BaseModel):
    """Standardized memory unit retrieved from Hindsight recall."""
    id: str = ""
    text: str
    type: str = "memory"
    context: str = ""
    entities: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    score: float = 0.0
    occurred_at: str = ""
    document_id: str = ""


class MeetingBrief(BaseModel):
    """Personalized AI Meeting Briefing synthesized by Groq + Hindsight."""
    client_name: str
    meeting_title: str
    meeting_date: str
    meeting_topic: str = ""
    objective: str = ""
    previous_discussions: str = ""
    key_decisions: List[str] = Field(default_factory=list)
    outstanding_commitments: List[str] = Field(default_factory=list)
    deadlines: List[str] = Field(default_factory=list)
    follow_ups: List[str] = Field(default_factory=list)
    client_preferences: List[str] = Field(default_factory=list)
    unresolved_issues: List[str] = Field(default_factory=list)
    suggested_questions: List[str] = Field(default_factory=list)
    risks_or_watchouts: List[str] = Field(default_factory=list)
    recommended_talking_points: List[str] = Field(default_factory=list)
    what_changed_since_last_meeting: str = ""
    memory_sources_count: int = 0
    raw_markdown: str = ""
