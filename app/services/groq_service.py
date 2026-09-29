"""Groq Service for LLM reasoning, note structuring, and meeting brief generation."""
import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from app.config import get_settings
from app.models.schemas import ExtractedNoteItems, MeetingBrief, RecalledMemoryItem
from app.utils.helpers import format_brief_markdown, parse_json_safely
from app.utils.prompts import (
    CLIENT_REFLECTION_SYSTEM_PROMPT,
    CLIENT_REFLECTION_USER_PROMPT,
    MEETING_PREP_SYSTEM_PROMPT,
    MEETING_PREP_USER_PROMPT,
    NOTE_EXTRACTION_SYSTEM_PROMPT,
    NOTE_EXTRACTION_USER_PROMPT,
)

logger = logging.getLogger(__name__)


class GroqService:
    """Manages LLM completions and reasoning with Groq API."""

    def __init__(self):
        self._client = None
        self._init_client()

    def _init_client(self):
        """Initialize Groq client if API key is configured."""
        settings = get_settings()
        if settings.has_groq_key:
            try:
                from groq import Groq
                self._client = Groq(api_key=settings.groq_api_key)
            except Exception as e:
                logger.error(f"Failed to initialize Groq client: {e}")
                self._client = None
        else:
            self._client = None

    @property
    def is_configured(self) -> bool:
        """Check if Groq API key is present."""
        settings = get_settings()
        return settings.has_groq_key

    def ping(self) -> Tuple[bool, str]:
        """Verify connectivity with Groq API."""
        if not self.is_configured:
            return False, "Groq API key not configured in .env"
        
        try:
            if not self._client:
                self._init_client()
            if not self._client:
                return False, "Groq client could not be initialized."
            
            models = self._client.models.list()
            return True, f"Connected to Groq API (Available models: {len(models.data)})"
        except Exception as e:
            return False, f"Groq connection error: {str(e)}"

    def extract_structured_notes(
        self,
        raw_notes: str,
        client_name: str,
        organization: str = "",
        topic: str = "",
        date_str: str = "",
    ) -> Tuple[bool, str, ExtractedNoteItems]:
        """
        Extract structured intelligence (decisions, commitments, deadlines,
        preferences, requirements, unresolved issues) from raw notes using Groq.
        """
        if not self.is_configured:
            return False, "Groq API key not configured. Please add GROQ_API_KEY to your .env file.", ExtractedNoteItems()

        if not raw_notes.strip():
            return False, "Raw meeting notes are empty.", ExtractedNoteItems()

        settings = get_settings()

        try:
            if not self._client:
                self._init_client()

            user_msg = NOTE_EXTRACTION_USER_PROMPT.format(
                client_name=client_name,
                organization=organization,
                topic=topic or "General Discussion",
                date_str=date_str or "Recent",
                raw_notes=raw_notes,
            )

            completion = self._client.chat.completions.create(
                model=settings.groq_model,
                messages=[
                    {"role": "system", "content": NOTE_EXTRACTION_SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
            )

            raw_content = completion.choices[0].message.content or "{}"
            parsed = parse_json_safely(raw_content, default={})

            extracted = ExtractedNoteItems(
                decisions=parsed.get("decisions", []),
                commitments=parsed.get("commitments", []),
                deadlines=parsed.get("deadlines", []),
                preferences=parsed.get("preferences", []),
                requirements=parsed.get("requirements", []),
                follow_ups=parsed.get("follow_ups", []),
                unresolved_issues=parsed.get("unresolved_issues", []),
            )

            return True, "Successfully extracted structured meeting intelligence.", extracted

        except Exception as e:
            logger.error(f"Groq note extraction failed: {e}", exc_info=True)
            return False, f"Groq extraction failed: {str(e)}", ExtractedNoteItems()

    def generate_meeting_brief(
        self,
        client_name: str,
        organization: str,
        meeting_title: str,
        meeting_date: str,
        meeting_topic: str,
        recalled_memories: List[RecalledMemoryItem],
    ) -> Tuple[bool, str, MeetingBrief]:
        """
        Synthesize recalled Hindsight memories + upcoming agenda with Groq
        to produce a personalized, context-aware Meeting Brief.
        """
        if not self.is_configured:
            return False, "Groq API key not configured. Please add GROQ_API_KEY to your .env file.", MeetingBrief(
                client_name=client_name,
                meeting_title=meeting_title,
                meeting_date=meeting_date,
                meeting_topic=meeting_topic,
                objective=f"Prepare for {meeting_title}",
            )

        settings = get_settings()

        try:
            if not self._client:
                self._init_client()

            # Format recalled memories into high-fidelity prompt context
            if recalled_memories:
                memory_lines = []
                for i, m in enumerate(recalled_memories, 1):
                    tags_str = f" [Tags: {', '.join(m.tags)}]" if m.tags else ""
                    ctx_str = f" ({m.context})" if m.context else ""
                    memory_lines.append(f"{i}. {m.text}{ctx_str}{tags_str}")
                recalled_text = "\n".join(memory_lines)
            else:
                recalled_text = "No prior memories recorded yet in Hindsight for this client (this appears to be the first meeting)."

            user_msg = MEETING_PREP_USER_PROMPT.format(
                client_name=client_name,
                organization=organization,
                meeting_title=meeting_title,
                meeting_date=meeting_date,
                meeting_topic=meeting_topic or "General Follow-up & Progress Review",
                recalled_memories_text=recalled_text,
            )

            completion = self._client.chat.completions.create(
                model=settings.groq_model,
                messages=[
                    {"role": "system", "content": MEETING_PREP_SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
            )

            raw_content = completion.choices[0].message.content or "{}"
            parsed = parse_json_safely(raw_content, default={})

            brief = MeetingBrief(
                client_name=client_name,
                meeting_title=meeting_title,
                meeting_date=meeting_date,
                meeting_topic=meeting_topic,
                objective=parsed.get("objective", f"Prepare for {meeting_title} with {client_name}"),
                previous_discussions=parsed.get("previous_discussions", ""),
                key_decisions=parsed.get("key_decisions", []),
                outstanding_commitments=parsed.get("outstanding_commitments", []),
                deadlines=parsed.get("deadlines", []),
                follow_ups=parsed.get("follow_ups", []),
                client_preferences=parsed.get("client_preferences", []),
                unresolved_issues=parsed.get("unresolved_issues", []),
                suggested_questions=parsed.get("suggested_questions", []),
                risks_or_watchouts=parsed.get("risks_or_watchouts", []),
                recommended_talking_points=parsed.get("recommended_talking_points", []),
                what_changed_since_last_meeting=parsed.get("what_changed_since_last_meeting", ""),
                memory_sources_count=len(recalled_memories),
            )

            # Generate beautiful markdown representation
            brief.raw_markdown = format_brief_markdown(brief)

            return True, "Personalized meeting brief generated successfully.", brief

        except Exception as e:
            logger.error(f"Groq brief generation failed: {e}", exc_info=True)
            empty_brief = MeetingBrief(
                client_name=client_name,
                meeting_title=meeting_title,
                meeting_date=meeting_date,
                meeting_topic=meeting_topic,
                objective=f"Failed to generate brief: {str(e)}",
            )
            return False, f"Brief generation failed: {str(e)}", empty_brief

    def reflect_client_relationship(
        self,
        client_name: str,
        organization: str,
        recalled_memories: List[RecalledMemoryItem],
    ) -> Tuple[bool, str]:
        """Synthesize executive relationship insights for a client using Groq."""
        if not self.is_configured:
            return False, "Groq API key not configured."

        if not recalled_memories:
            return False, f"No memories found in Hindsight for {client_name} yet. Record notes from meetings first to build memory."

        settings = get_settings()

        try:
            if not self._client:
                self._init_client()

            memory_lines = [f"- {m.text} (Context: {m.context})" for m in recalled_memories]
            recalled_text = "\n".join(memory_lines)

            user_msg = CLIENT_REFLECTION_USER_PROMPT.format(
                client_name=client_name,
                organization=organization,
                recalled_memories_text=recalled_text,
            )

            completion = self._client.chat.completions.create(
                model=settings.groq_model,
                messages=[
                    {"role": "system", "content": CLIENT_REFLECTION_SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.3,
            )

            insight = completion.choices[0].message.content or ""
            return True, insight

        except Exception as e:
            logger.error(f"Client reflection failed: {e}", exc_info=True)
            return False, f"Reflection failed: {str(e)}"


# Global singleton instance
groq_service = GroqService()


def get_groq_service() -> GroqService:
    """Return the global GroqService instance."""
    return groq_service
