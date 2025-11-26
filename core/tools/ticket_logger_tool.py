"""
Ticket Logger Tool

- Validates ticket payloads
- Appends them to tickets.csv via code_execution_tool
"""

import logging
from datetime import datetime, timezone
import pandas as pd

from core.tools.code_execution_tool import exec_read_csv, exec_write_csv

logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[TICKET_LOGGER] %(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


REQUIRED_FIELDS = [
    "creator_id",
    "email_id",
    "type",
    "title",
    "description",
    "priority",
]


def _utc_now_iso() -> str:
    """UTC timestamp in ISO format with Z suffix."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _load_tickets_df() -> pd.DataFrame:
    """Load tickets.csv via safe code execution tool."""
    rows = exec_read_csv("tickets.csv")
    return pd.DataFrame(rows)


def _validate_and_normalize(ticket_data: dict, existing_df: pd.DataFrame) -> dict:
    """Validate required fields and normalize into a full row dict."""
    if not isinstance(ticket_data, dict):
        raise ValueError("ticket_data must be a dict.")

    missing = [f for f in REQUIRED_FIELDS if f not in ticket_data or ticket_data[f] in (None, "")]
    if missing:
        raise ValueError(f"Missing required ticket fields: {missing}")

    # Compute next ticket_id
    if not existing_df.empty and "ticket_id" in existing_df.columns:
        # assume numeric ids
        max_id = existing_df["ticket_id"].astype(int).max()
        next_id = int(max_id) + 1
    else:
        next_id = 1

    now = _utc_now_iso()

    row = {
        "ticket_id": next_id,
        "creator_id": ticket_data["creator_id"],
        "email_id": ticket_data["email_id"],
        "type": ticket_data["type"],
        "title": ticket_data["title"],
        "description": ticket_data["description"],
        "priority": ticket_data["priority"],
        # Defaults if not provided
        "status": ticket_data.get("status", "open"),
        "created_by": ticket_data.get("created_by", "orchestrator_agent"),
        "assigned_to": ticket_data.get("assigned_to", "inbox_manager"),
        "created_datetime_utc": ticket_data.get("created_datetime_utc", now),
        "updated_datetime_utc": ticket_data.get("updated_datetime_utc", now),
        "due_datetime_utc": ticket_data.get("due_datetime_utc", ""),
        "resolution_notes": ticket_data.get("resolution_notes", ""),
    }

    return row


def log_ticket(ticket_data: dict) -> dict:
    """
    Validate and append a new ticket row to tickets.csv.

    Returns:
        The created ticket row as a dict.
    """
    logger.info(f"log_ticket called with payload keys: {list(ticket_data.keys())}")

    df = _load_tickets_df()
    new_row = _validate_and_normalize(ticket_data, df)

    # Append and persist
    updated_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    exec_write_csv(updated_df, "tickets.csv")

    logger.info(f"Ticket logged with ticket_id={new_row['ticket_id']}")
    return new_row
