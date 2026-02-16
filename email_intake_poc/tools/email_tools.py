from __future__ import annotations
from typing import Any, Dict, List

from ..clients.graph_client import GraphMailClient

_graph = GraphMailClient()

def read_unread_inbox(top: int = 10) -> List[Dict[str, Any]]:
    """
    Tool: Returns unread emails (top N) from Inbox.
    """
    return _graph.list_inbox_messages(top=top, unread_only=True)

def read_latest_inbox(top: int = 10) -> List[Dict[str, Any]]:
    """
    Tool: Returns latest emails (read + unread) (top N) from Inbox.
    """
    return _graph.list_inbox_messages(top=top, unread_only=False)

def read_message_full(message_id: str, prefer_text: bool = True) -> Dict[str, Any]:
    """
    Tool: Returns full message details including body.
    """
    return _graph.get_message(message_id=message_id, prefer_text=prefer_text)

def mark_message_read(message_id: str) -> Dict[str, Any]:
    """
    Tool: Marks an email as read.
    """
    _graph.mark_as_read(message_id=message_id)
    return {"status": "ok", "message_id": message_id}
