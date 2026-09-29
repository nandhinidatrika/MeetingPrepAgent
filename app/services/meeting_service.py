"""Meeting Service coordinating SQLite metadata, Hindsight long-term memory, and Groq LLM reasoning."""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from app.database import db
from app.models.schemas import (
    ActionLog,
    Client,
    ExtractedNoteItems,
    FollowUp,
    Meeting,
    MeetingBrief,
    MemoryPayload,
    RecalledMemoryItem,
)
from app.services.groq_service import get_groq_service
from app.services.hindsight_service import get_hindsight_service

logger = logging.getLogger(__name__)


class MeetingService:
    """Core orchestrator for meeting preparation, note retention, and memory workflows."""

    def __init__(self):
        self.hindsight = get_hindsight_service()
        self.groq = get_groq_service()

    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Fetch summary metrics and system status for dashboard."""
        clients = db.get_all_clients()
        meetings = db.get_all_meetings()
        pending_followups = db.get_pending_follow_ups()
        recent_actions = db.get_recent_actions(limit=8)

        prepared_count = sum(1 for m in meetings if m.status == "prepared" or m.brief_cache)
        upcoming_count = sum(1 for m in meetings if m.status == "upcoming")
        completed_count = sum(1 for m in meetings if m.status == "completed")

        hindsight_ok, hindsight_msg = self.hindsight.ping()
        groq_ok, groq_msg = self.groq.ping()

        return {
            "total_clients": len(clients),
            "total_meetings": len(meetings),
            "upcoming_meetings": upcoming_count,
            "prepared_briefs": prepared_count,
            "completed_meetings": completed_count,
            "pending_followups_count": len(pending_followups),
            "pending_followups": pending_followups,
            "recent_actions": recent_actions,
            "recent_meetings": meetings[:6],
            "hindsight_status": {"ok": hindsight_ok, "message": hindsight_msg},
            "groq_status": {"ok": groq_ok, "message": groq_msg},
        }

    def prepare_meeting(
        self,
        client_id: str,
        meeting_id: str,
        topic: str = "",
    ) -> Tuple[bool, str, Optional[MeetingBrief], List[RecalledMemoryItem]]:
        """
        Execute Pre-Meeting Preparation Workflow:
        1. Query client and meeting details from SQLite.
        2. Recall all relevant historical memories from Hindsight Cloud.
        3. Send recalled memory context + agenda to Groq LLM.
        4. Synthesize personalized Meeting Brief.
        5. Save brief cache to SQLite and log action.
        """
        client = db.get_client_by_id(client_id)
        if not client:
            return False, "Client not found in database.", None, []

        meeting = db.get_meeting_by_id(meeting_id)
        if not meeting:
            return False, "Meeting not found in database.", None, []

        active_topic = topic.strip() or meeting.topic or meeting.title

        # Step 1: Recall from Hindsight Cloud
        search_query = f"Background, preferences, commitments, decisions, deadlines, and technical requirements for {client.name} regarding {active_topic}"
        recalled_memories = self.hindsight.recall_memories(
            query=search_query,
            client_name=client.name,
            max_tokens=4096,
        )

        # Step 2: Groq Reasoning & Brief Synthesis
        ok, msg, brief = self.groq.generate_meeting_brief(
            client_name=client.name,
            organization=client.organization,
            meeting_title=meeting.title,
            meeting_date=meeting.meeting_date,
            meeting_topic=active_topic,
            recalled_memories=recalled_memories,
        )

        if ok and brief:
            # Step 3: Update SQLite metadata
            db.update_meeting(
                meeting_id=meeting.id,
                topic=active_topic,
                status="prepared",
                brief_cache=brief.raw_markdown,
            )
            db.log_action(
                action_type="prepare",
                summary=f"Generated AI Brief for '{meeting.title}' ({len(recalled_memories)} memories recalled)",
                client_id=client.id,
                meeting_id=meeting.id,
            )
            return True, f"Meeting brief generated successfully using {len(recalled_memories)} Hindsight memories.", brief, recalled_memories
        
        return False, msg, brief, recalled_memories

    def save_and_remember_post_meeting(
        self,
        client_id: str,
        meeting_id: str,
        raw_notes: str,
        extracted_items: ExtractedNoteItems,
        retain_to_hindsight: bool = True,
    ) -> Tuple[bool, str, List[str]]:
        """
        Execute Post-Meeting Memory Retention Workflow:
        1. Save meeting notes & status to SQLite metadata.
        2. Create follow-up tasks in SQLite.
        3. Structure memory payload and retain into Hindsight Cloud.
        4. Log retention audit record.
        """
        client = db.get_client_by_id(client_id)
        if not client:
            return False, "Client not found.", []

        meeting = db.get_meeting_by_id(meeting_id)
        if not meeting:
            return False, "Meeting not found.", []

        # 1. Update SQLite meeting status and notes
        db.update_meeting(
            meeting_id=meeting_id,
            notes=raw_notes.strip(),
            status="completed",
        )

        # 2. Add extracted follow-ups & commitments to SQLite follow_ups table
        action_tasks = list(dict.fromkeys(extracted_items.follow_ups + extracted_items.commitments))
        for item in action_tasks:
            db.create_follow_up(
                meeting_id=meeting_id,
                client_id=client_id,
                task=item,
                owner="Me",
                due_date=meeting.meeting_date,
            )

        retained_chunks: List[str] = []

        # 3. Retain into Hindsight Cloud
        if retain_to_hindsight:
            payload = MemoryPayload(
                client_id=client.id,
                client_name=client.name,
                organization=client.organization,
                meeting_id=meeting.id,
                meeting_title=meeting.title,
                meeting_date=meeting.meeting_date,
                topic=meeting.topic or meeting.title,
                items=extracted_items,
                raw_notes=raw_notes,
            )

            h_ok, h_msg, chunks = self.hindsight.retain_meeting_memory(payload)
            retained_chunks = chunks

            db.log_action(
                action_type="retain",
                summary=f"Retained {len(chunks)} memory units into Hindsight for '{meeting.title}'",
                client_id=client.id,
                meeting_id=meeting.id,
            )

            if not h_ok:
                return False, f"Notes saved locally, but Hindsight memory retention encountered an error: {h_msg}", retained_chunks

        return True, f"Meeting notes recorded and {len(retained_chunks)} memories retained into Hindsight Cloud!", retained_chunks

    def seed_demo_scenario(self, retain_to_hindsight: bool = True) -> Dict[str, Any]:
        """
        Initialize the complete 3-Meeting ABC Technologies evolution demo dataset.
        Demonstrates the core value loop:
        Meeting 1: Initial scope & preferences -> Retained to Hindsight
        Meeting 2: Changed deadlines, regional filters, twice-weekly updates, Okta auth blocker -> Retained to Hindsight
        Meeting 3: Upcoming meeting ready for preparation to demonstrate combined Old + New memory recall!
        """
        # Ensure DB is initialized
        db.init_db()

        # Check or create ABC Technologies client
        existing_client = db.get_client_by_name("Sarah Chen")
        if existing_client:
            client = existing_client
        else:
            client = db.create_client(
                name="Sarah Chen",
                organization="ABC Technologies",
                email="sarah.chen@abctechnologies.io",
                role="VP of Engineering",
                notes="Primary engineering stakeholder for analytics and API integrations.",
            )

        # ----------------------------------------------------------------------
        # Meeting 1: Initial Requirements (Historical)
        # ----------------------------------------------------------------------
        m1_notes = (
            "Kickoff meeting with ABC Technologies. They need a custom analytics dashboard. "
            "Target launch deadline is October 15. Sarah emphasized that comprehensive API "
            "documentation is strictly required before any production deployment. "
            "Client explicitly stated they prefer concise bulleted progress updates. "
            "Agreed to deliver draft UI wireframes by this Friday."
        )
        m1_items = ExtractedNoteItems(
            decisions=["Build custom analytics dashboard", "Deliver draft UI wireframes by Friday"],
            commitments=["Provide comprehensive API documentation before production launch"],
            deadlines=["Analytics dashboard launch: October 15"],
            preferences=["Client prefers concise bulleted updates only"],
            requirements=["Custom analytics dashboard", "Complete API documentation"],
            follow_ups=["Send draft UI wireframes by Friday"],
            unresolved_issues=[],
        )

        m1 = db.create_meeting(
            client_id=client.id,
            title="Meeting 1: Analytics Dashboard Kickoff",
            meeting_date="2026-09-01",
            meeting_time="10:00 AM",
            topic="Analytics Dashboard Requirements & Timeline",
            status="completed",
            notes=m1_notes,
        )

        m1_retained_count = 0
        if retain_to_hindsight and self.hindsight.is_configured:
            payload1 = MemoryPayload(
                client_id=client.id,
                client_name=client.name,
                organization=client.organization,
                meeting_id=m1.id,
                meeting_title=m1.title,
                meeting_date=m1.meeting_date,
                topic=m1.topic,
                items=m1_items,
                raw_notes=m1_notes,
            )
            _, _, chunks1 = self.hindsight.retain_meeting_memory(payload1)
            m1_retained_count = len(chunks1)

        # ----------------------------------------------------------------------
        # Meeting 2: Scope Shift & Cadence Update (Historical)
        # ----------------------------------------------------------------------
        m2_notes = (
            "Mid-sprint review with Sarah Chen. Major updates: "
            "1. Dashboard scope expanded: must include regional filtering for North America and Europe. "
            "2. API documentation deadline shifted to October 25 due to backend API schema changes. "
            "3. Sarah requested progress updates twice per week (every Tuesday & Thursday). "
            "4. Critical unresolved issue: Enterprise Okta SSO authentication integration is currently blocked by their IT security review."
        )
        m2_items = ExtractedNoteItems(
            decisions=["Add regional filtering (NA and EU) to dashboard scope", "Shift API documentation deadline to October 25"],
            commitments=["Provide progress updates twice per week (Tuesday & Thursday)"],
            deadlines=["API documentation shifted deadline: October 25", "Dashboard launch deadline: October 15"],
            preferences=["Progress update frequency: Twice per week (Tue/Thu)", "Concise updates"],
            requirements=["Regional filtering across NA & EU", "Enterprise Okta SSO authentication"],
            follow_ups=["Follow up with ABC Tech IT security team on Okta SSO approval"],
            unresolved_issues=["Enterprise Okta SSO authentication blocker pending IT security review"],
        )

        m2 = db.create_meeting(
            client_id=client.id,
            title="Meeting 2: Mid-Sprint Review & Scope Expansion",
            meeting_date="2026-09-15",
            meeting_time="02:00 PM",
            topic="Scope Expansion, Timeline Adjustment & Auth Blocker",
            status="completed",
            notes=m2_notes,
        )

        m2_retained_count = 0
        if retain_to_hindsight and self.hindsight.is_configured:
            payload2 = MemoryPayload(
                client_id=client.id,
                client_name=client.name,
                organization=client.organization,
                meeting_id=m2.id,
                meeting_title=m2.title,
                meeting_date=m2.meeting_date,
                topic=m2.topic,
                items=m2_items,
                raw_notes=m2_notes,
            )
            _, _, chunks2 = self.hindsight.retain_meeting_memory(payload2)
            m2_retained_count = len(chunks2)

        # ----------------------------------------------------------------------
        # Meeting 3: Upcoming Pre-Launch Alignment (Ready for "Prepare Me")
        # ----------------------------------------------------------------------
        m3 = db.create_meeting(
            client_id=client.id,
            title="Meeting 3: Auth Blocker Resolution & Final Pre-Launch Review",
            meeting_date="2026-10-01",
            meeting_time="11:00 AM",
            topic="Resolving Okta SSO Blocker, Regional Filtering Verification, and Launch Prep",
            status="upcoming",
            notes="",
        )

        # Seed initial follow up task
        db.create_follow_up(
            meeting_id=m2.id,
            client_id=client.id,
            task="Confirm Okta SSO authentication status with IT security",
            owner="Me",
            due_date="2026-09-28",
        )

        db.log_action(
            action_type="retain",
            summary=f"Seeded ABC Technologies Demo Scenario ({m1_retained_count + m2_retained_count} memories retained in Hindsight)",
            client_id=client.id,
            meeting_id=m3.id,
        )

        return {
            "client": client,
            "meetings": [m1, m2, m3],
            "m1_retained": m1_retained_count,
            "m2_retained": m2_retained_count,
            "total_retained": m1_retained_count + m2_retained_count,
        }


# Global singleton instance
meeting_service = MeetingService()


def get_meeting_service() -> MeetingService:
    """Return the global MeetingService instance."""
    return meeting_service
