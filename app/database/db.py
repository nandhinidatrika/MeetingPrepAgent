"""SQLite Database operations for Meeting Prep Agent application metadata."""
import os
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from app.config import get_settings
from app.models.schemas import ActionLog, Client, FollowUp, Meeting


def get_db_connection() -> sqlite3.Connection:
    """Create and return a SQLite database connection with row factory."""
    settings = get_settings()
    db_path = Path(settings.sqlite_db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database tables and indexes."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Clients table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            organization TEXT DEFAULT '',
            email TEXT DEFAULT '',
            role TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    # Meetings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS meetings (
            id TEXT PRIMARY KEY,
            client_id TEXT NOT NULL,
            title TEXT NOT NULL,
            meeting_date TEXT NOT NULL,
            meeting_time TEXT DEFAULT '10:00 AM',
            status TEXT DEFAULT 'upcoming',
            topic TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            raw_transcript TEXT DEFAULT '',
            brief_cache TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
        )
    """)

    # Follow-ups table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS follow_ups (
            id TEXT PRIMARY KEY,
            meeting_id TEXT NOT NULL,
            client_id TEXT NOT NULL,
            task TEXT NOT NULL,
            owner TEXT DEFAULT 'Me',
            due_date TEXT DEFAULT '',
            status TEXT DEFAULT 'pending',
            created_at TEXT NOT NULL,
            FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE,
            FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
        )
    """)

    # Action logs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS action_logs (
            id TEXT PRIMARY KEY,
            client_id TEXT DEFAULT '',
            meeting_id TEXT DEFAULT '',
            action_type TEXT NOT NULL,
            summary TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_meetings_client ON meetings(client_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_followups_client ON follow_ups(client_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_followups_status ON follow_ups(status);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_actionlogs_date ON action_logs(created_at);")

    conn.commit()
    conn.close()


# ------------------------------------------------------------------------------
# Clients CRUD
# ------------------------------------------------------------------------------
def get_all_clients() -> List[Client]:
    """Retrieve all clients ordered by name."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clients ORDER BY name ASC")
    rows = cursor.fetchall()
    conn.close()
    return [Client(**dict(row)) for row in rows]


def get_client_by_id(client_id: str) -> Optional[Client]:
    """Retrieve a single client by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clients WHERE id = ?", (client_id,))
    row = cursor.fetchone()
    conn.close()
    return Client(**dict(row)) if row else None


def get_client_by_name(name: str) -> Optional[Client]:
    """Retrieve a single client by name."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clients WHERE LOWER(name) = LOWER(?)", (name.strip(),))
    row = cursor.fetchone()
    conn.close()
    return Client(**dict(row)) if row else None


def create_client(name: str, organization: str = "", email: str = "", role: str = "", notes: str = "") -> Client:
    """Create a new client entity in SQLite."""
    client_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    client = Client(
        id=client_id,
        name=name.strip(),
        organization=organization.strip(),
        email=email.strip(),
        role=role.strip(),
        notes=notes.strip(),
        created_at=now,
        updated_at=now
    )
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO clients (id, name, organization, email, role, notes, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (client.id, client.name, client.organization, client.email, client.role, client.notes, client.created_at, client.updated_at))
    conn.commit()
    conn.close()
    return client


def update_client(client_id: str, **kwargs) -> Optional[Client]:
    """Update client fields."""
    client = get_client_by_id(client_id)
    if not client:
        return None
    
    updated_dict = client.model_dump()
    for k, v in kwargs.items():
        if k in updated_dict and k not in ["id", "created_at"]:
            updated_dict[k] = v
    updated_dict["updated_at"] = datetime.now().isoformat()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE clients 
        SET name = ?, organization = ?, email = ?, role = ?, notes = ?, updated_at = ?
        WHERE id = ?
    """, (
        updated_dict["name"],
        updated_dict["organization"],
        updated_dict["email"],
        updated_dict["role"],
        updated_dict["notes"],
        updated_dict["updated_at"],
        client_id
    ))
    conn.commit()
    conn.close()
    return Client(**updated_dict)


def delete_client(client_id: str):
    """Delete client and associated records."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM follow_ups WHERE client_id = ?", (client_id,))
    cursor.execute("DELETE FROM meetings WHERE client_id = ?", (client_id,))
    cursor.execute("DELETE FROM clients WHERE id = ?", (client_id,))
    conn.commit()
    conn.close()


# ------------------------------------------------------------------------------
# Meetings CRUD
# ------------------------------------------------------------------------------
def get_all_meetings() -> List[Meeting]:
    """Retrieve all meetings ordered by meeting date desc."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM meetings ORDER BY meeting_date DESC, created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [Meeting(**dict(row)) for row in rows]


def get_meetings_by_client(client_id: str) -> List[Meeting]:
    """Retrieve all meetings for a specific client."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM meetings WHERE client_id = ? ORDER BY meeting_date ASC", (client_id,))
    rows = cursor.fetchall()
    conn.close()
    return [Meeting(**dict(row)) for row in rows]


def get_meeting_by_id(meeting_id: str) -> Optional[Meeting]:
    """Retrieve a single meeting by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM meetings WHERE id = ?", (meeting_id,))
    row = cursor.fetchone()
    conn.close()
    return Meeting(**dict(row)) if row else None


def create_meeting(
    client_id: str,
    title: str,
    meeting_date: str,
    meeting_time: str = "10:00 AM",
    topic: str = "",
    status: str = "upcoming",
    notes: str = "",
    raw_transcript: str = ""
) -> Meeting:
    """Create a new meeting entry."""
    meeting_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    meeting = Meeting(
        id=meeting_id,
        client_id=client_id,
        title=title.strip(),
        meeting_date=meeting_date,
        meeting_time=meeting_time,
        status=status,
        topic=topic.strip(),
        notes=notes.strip(),
        raw_transcript=raw_transcript.strip(),
        brief_cache="",
        created_at=now,
        updated_at=now
    )
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO meetings (id, client_id, title, meeting_date, meeting_time, status, topic, notes, raw_transcript, brief_cache, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        meeting.id, meeting.client_id, meeting.title, meeting.meeting_date,
        meeting.meeting_time, meeting.status, meeting.topic, meeting.notes,
        meeting.raw_transcript, meeting.brief_cache, meeting.created_at, meeting.updated_at
    ))
    conn.commit()
    conn.close()
    return meeting


def update_meeting(meeting_id: str, **kwargs) -> Optional[Meeting]:
    """Update meeting fields."""
    meeting = get_meeting_by_id(meeting_id)
    if not meeting:
        return None
    
    updated_dict = meeting.model_dump()
    for k, v in kwargs.items():
        if k in updated_dict and k not in ["id", "created_at"]:
            updated_dict[k] = v
    updated_dict["updated_at"] = datetime.now().isoformat()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE meetings
        SET client_id = ?, title = ?, meeting_date = ?, meeting_time = ?, status = ?, topic = ?, notes = ?, raw_transcript = ?, brief_cache = ?, updated_at = ?
        WHERE id = ?
    """, (
        updated_dict["client_id"], updated_dict["title"], updated_dict["meeting_date"],
        updated_dict["meeting_time"], updated_dict["status"], updated_dict["topic"],
        updated_dict["notes"], updated_dict["raw_transcript"], updated_dict["brief_cache"],
        updated_dict["updated_at"], meeting_id
    ))
    conn.commit()
    conn.close()
    return Meeting(**updated_dict)


def delete_meeting(meeting_id: str):
    """Delete a meeting and associated follow-ups."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM follow_ups WHERE meeting_id = ?", (meeting_id,))
    cursor.execute("DELETE FROM meetings WHERE id = ?", (meeting_id,))
    conn.commit()
    conn.close()


# ------------------------------------------------------------------------------
# Follow-Ups CRUD
# ------------------------------------------------------------------------------
def get_all_follow_ups() -> List[FollowUp]:
    """Retrieve all follow-up action items."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM follow_ups ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [FollowUp(**dict(row)) for row in rows]


def get_pending_follow_ups(client_id: Optional[str] = None) -> List[FollowUp]:
    """Retrieve pending follow-up items, optionally filtered by client."""
    conn = get_db_connection()
    cursor = conn.cursor()
    if client_id:
        cursor.execute("SELECT * FROM follow_ups WHERE status = 'pending' AND client_id = ? ORDER BY created_at DESC", (client_id,))
    else:
        cursor.execute("SELECT * FROM follow_ups WHERE status = 'pending' ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [FollowUp(**dict(row)) for row in rows]


def create_follow_up(meeting_id: str, client_id: str, task: str, owner: str = "Me", due_date: str = "") -> FollowUp:
    """Create a new follow-up task."""
    item_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    follow_up = FollowUp(
        id=item_id,
        meeting_id=meeting_id,
        client_id=client_id,
        task=task.strip(),
        owner=owner.strip(),
        due_date=due_date.strip(),
        status="pending",
        created_at=now
    )
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO follow_ups (id, meeting_id, client_id, task, owner, due_date, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (follow_up.id, follow_up.meeting_id, follow_up.client_id, follow_up.task, follow_up.owner, follow_up.due_date, follow_up.status, follow_up.created_at))
    conn.commit()
    conn.close()
    return follow_up


def toggle_follow_up_status(follow_up_id: str, completed: bool) -> bool:
    """Toggle follow-up status between pending and completed."""
    new_status = "completed" if completed else "pending"
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE follow_ups SET status = ? WHERE id = ?", (new_status, follow_up_id))
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()
    return rows_affected > 0


def delete_follow_up(follow_up_id: str):
    """Delete a follow-up item."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM follow_ups WHERE id = ?", (follow_up_id,))
    conn.commit()
    conn.close()


# ------------------------------------------------------------------------------
# Action Logs
# ------------------------------------------------------------------------------
def log_action(action_type: str, summary: str, client_id: str = "", meeting_id: str = "") -> ActionLog:
    """Record an audit action log."""
    log_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    action = ActionLog(
        id=log_id,
        client_id=client_id,
        meeting_id=meeting_id,
        action_type=action_type,
        summary=summary,
        created_at=now
    )
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO action_logs (id, client_id, meeting_id, action_type, summary, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (action.id, action.client_id, action.meeting_id, action.action_type, action.summary, action.created_at))
    conn.commit()
    conn.close()
    return action


def get_recent_actions(limit: int = 15) -> List[ActionLog]:
    """Retrieve recent action logs."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM action_logs ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [ActionLog(**dict(row)) for row in rows]


def reset_db():
    """Reset / clear database tables."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS follow_ups")
    cursor.execute("DROP TABLE IF EXISTS meetings")
    cursor.execute("DROP TABLE IF EXISTS clients")
    cursor.execute("DROP TABLE IF EXISTS action_logs")
    conn.commit()
    conn.close()
    init_db()
