
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class Email:
    """
    Normalized view of an email row from inbox.csv.
    """
    email_id: int
    thread_id: int
    creator_id: str
    from_name: str
    from_email: str
    to_email: str
    subject: str
    body_text: str
    category: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    metadata: Dict[str, Any] = None


@dataclass
class TriageResult:
    """
    Output from TriageAgent.
    """
    email_id: int
    category: str
    priority: str
    ticket_suggestion: Optional[Dict[str, Any]] = None  # e.g. {"needed": True, "type": "...", "reason": "..."}


@dataclass
class KBContext:
    """
    Output from KnowledgeBaseAgent.
    """
    email_id: int
    kb_entries: List[Dict[str, Any]]  # KB entries
    debug_info: Optional[Dict[str, Any]] = None


@dataclass
class ReplyResult:
    """
    Output from ReplyAgent._
    """
    email_id: int
    reply_subject: str
    reply_body: str
    follow_up_action: Optional[Dict[str, Any]] = None  # {"create_ticket": True, "ticket_payload": {...}}
    notes: Optional[str] = None  # stored in inbox.csv.notes
