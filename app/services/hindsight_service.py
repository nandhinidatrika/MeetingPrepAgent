"""Hindsight Cloud Service for persistent long-term agent memory.

Official Documentation: https://hindsight.vectorize.io
Official Python SDK: hindsight-client
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import requests
from app.config import get_settings
from app.models.schemas import MemoryPayload, RecalledMemoryItem
from app.utils.helpers import build_memory_chunks

logger = logging.getLogger(__name__)


class HindsightService:
    """Manages long-term persistent memory operations with Hindsight Cloud."""

    def __init__(self):
        self._client = None
        self._init_client()

    def _init_client(self):
        """Initialize Hindsight SDK client if credentials are configured."""
        settings = get_settings()
        if settings.has_hindsight_key:
            try:
                from hindsight_client import Hindsight
                self._client = Hindsight(
                    base_url=settings.hindsight_api_url,
                    api_key=settings.hindsight_api_key,
                    timeout=30.0,
                )
            except Exception as e:
                logger.error(f"Failed to initialize Hindsight client: {e}")
                self._client = None
        else:
            self._client = None

    @property
    def is_configured(self) -> bool:
        """Check if Hindsight API credentials are fully configured."""
        settings = get_settings()
        return settings.has_hindsight_key

    def ping(self) -> Tuple[bool, str]:
        """Verify connectivity and authentication with Hindsight Cloud."""
        if not self.is_configured:
            return False, "Hindsight API key not configured in .env"
        
        settings = get_settings()
        try:
            # Check version or ping endpoint
            if self._client:
                try:
                    version = self._client.get_version()
                    return True, f"Connected to Hindsight Cloud (API Version: {getattr(version, 'version', 'active')})"
                except Exception:
                    pass
            
            # Direct HTTP check
            headers = {"Authorization": f"Bearer {settings.hindsight_api_key}"}
            resp = requests.get(f"{settings.hindsight_api_url.rstrip('/')}/health", headers=headers, timeout=10)
            if resp.status_code in [200, 204]:
                return True, "Connected to Hindsight Cloud"
            return True, f"Hindsight Cloud reachable (Status: {resp.status_code})"
        except Exception as e:
            return False, f"Hindsight connection error: {str(e)}"

    def retain_meeting_memory(
        self,
        payload: MemoryPayload,
        bank_id: Optional[str] = None,
    ) -> Tuple[bool, str, List[str]]:
        """
        Retain structured meeting notes, decisions, commitments, preferences,
        and requirements into Hindsight Cloud long-term memory.
        """
        if not self.is_configured:
            return False, "Hindsight API key is missing. Please add HINDSIGHT_API_KEY to your .env file.", []

        settings = get_settings()
        target_bank = bank_id or settings.hindsight_bank_id
        chunks = build_memory_chunks(payload)
        retained_summaries: List[str] = []

        try:
            # Re-init client if needed
            if not self._client:
                self._init_client()

            if not self._client:
                return False, "Hindsight client could not be initialized.", []

            doc_id = f"meeting_{payload.meeting_id}"

            for chunk in chunks:
                content = chunk["content"]
                context = chunk.get("context", f"Meeting with {payload.client_name}")
                tags = chunk.get("tags", [])

                # Retain each chunk into Hindsight Cloud
                self._client.retain(
                    bank_id=target_bank,
                    content=content,
                    context=context,
                    tags=tags,
                    document_id=doc_id,
                )
                retained_summaries.append(content)

            return True, f"Successfully retained {len(chunks)} memory units into Hindsight Cloud bank '{target_bank}'.", retained_summaries

        except Exception as e:
            logger.error(f"Hindsight retain error: {e}", exc_info=True)
            return False, f"Hindsight retain failed: {str(e)}", retained_summaries

    def recall_memories(
        self,
        query: str,
        client_name: Optional[str] = None,
        bank_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        max_tokens: int = 4096,
    ) -> List[RecalledMemoryItem]:
        """
        Recall relevant historical memories from Hindsight Cloud using TEMPR multi-strategy search.
        """
        if not self.is_configured:
            logger.warning("Hindsight not configured. Returning empty memory recall.")
            return []

        settings = get_settings()
        target_bank = bank_id or settings.hindsight_bank_id

        try:
            if not self._client:
                self._init_client()

            if not self._client:
                return []

            # Enhance query with client name if provided for higher recall relevance
            full_query = f"{client_name}: {query}" if client_name else query

            search_tags = list(tags) if tags else []
            if client_name:
                search_tags.append(f"client:{client_name.lower().replace(' ', '_')}")

            # Call official Hindsight recall
            response = self._client.recall(
                bank_id=target_bank,
                query=full_query,
                tags=search_tags if search_tags else None,
                max_tokens=max_tokens,
            )

            recalled_items: List[RecalledMemoryItem] = []
            results = getattr(response, "results", []) or []

            for res in results:
                text = getattr(res, "text", "") or ""
                if not text:
                    continue
                
                item_id = str(getattr(res, "id", "") or "")
                mem_type = str(getattr(res, "type", "memory") or "memory")
                context = str(getattr(res, "context", "") or "")
                entities = getattr(res, "entities", []) or []
                res_tags = getattr(res, "tags", []) or []
                score = float(getattr(res, "scores", {}).get("overall", 0.0) if hasattr(res, "scores") and isinstance(res.scores, dict) else 0.0)
                occurred = str(getattr(res, "occurred_start", "") or getattr(res, "mentioned_at", "") or "")
                doc_id = str(getattr(res, "document_id", "") or "")

                recalled_items.append(
                    RecalledMemoryItem(
                        id=item_id,
                        text=text,
                        type=mem_type,
                        context=context,
                        entities=[str(e) for e in entities],
                        tags=[str(t) for t in res_tags],
                        score=score,
                        occurred_at=occurred,
                        document_id=doc_id,
                    )
                )

            return recalled_items

        except Exception as e:
            logger.error(f"Hindsight recall error: {e}", exc_info=True)
            return []

    def list_client_memories(
        self,
        client_name: str,
        bank_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[RecalledMemoryItem]:
        """Retrieve memory units associated with a client for exploration."""
        if not self.is_configured:
            return []

        settings = get_settings()
        target_bank = bank_id or settings.hindsight_bank_id

        try:
            if not self._client:
                self._init_client()

            if not self._client:
                return []

            # Try list_memories first
            try:
                tag = f"client:{client_name.lower().replace(' ', '_')}"
                resp = self._client.list_memories(
                    bank_id=target_bank,
                    search_query=client_name,
                    limit=limit,
                )
                items = getattr(resp, "items", []) or []
                if items:
                    out = []
                    for it in items:
                        out.append(
                            RecalledMemoryItem(
                                id=str(getattr(it, "id", "")),
                                text=str(getattr(it, "text", "") or getattr(it, "content", "")),
                                type=str(getattr(it, "type", "memory")),
                                context=str(getattr(it, "context", "")),
                                tags=getattr(it, "tags", []) or [],
                                occurred_at=str(getattr(it, "occurred_start", "") or getattr(it, "created_at", "")),
                            )
                        )
                    return out
            except Exception:
                pass

            # Fallback to broad recall
            return self.recall_memories(
                query=f"All background, decisions, deadlines, preferences, and requirements for {client_name}",
                client_name=client_name,
                bank_id=target_bank,
                max_tokens=6000,
            )

        except Exception as e:
            logger.error(f"Hindsight list memories error: {e}")
            return []

    def reflect(self, client_name: str, bank_id: Optional[str] = None) -> Optional[str]:
        """Perform agent reflection / synthesis on a client's long-term history."""
        if not self.is_configured or not self._client:
            return None

        settings = get_settings()
        target_bank = bank_id or settings.hindsight_bank_id

        try:
            query = f"Synthesize all interactions, personality, working style, and trajectory for {client_name}"
            resp = self._client.reflect(bank_id=target_bank, query=query)
            if resp:
                if hasattr(resp, "text"):
                    return resp.text
                if hasattr(resp, "insight"):
                    return resp.insight
                if hasattr(resp, "response"):
                    return resp.response
                return str(resp)
        except Exception as e:
            logger.warning(f"Hindsight reflect not available or error: {e}")
            return None


# Global singleton instance
hindsight_service = HindsightService()


def get_hindsight_service() -> HindsightService:
    """Return the global HindsightService instance."""
    return hindsight_service
