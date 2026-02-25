from __future__ import annotations
from typing import Any, Dict, List
from unittest import result


from ..clients.graph_client import GraphMailClient

from google.adk.tools.tool_context  import ToolContext 

_graph = GraphMailClient()

def read_unread_inbox(tool_context: ToolContext, top: int = 10) -> List[Dict[str, Any]]:
    """
    Tool: Returns unread emails (top N) from Inbox.
    """
    result = _graph.list_inbox_messages(top=top, unread_only=True)
    #tool_context.state["unread_email_list"] = result
    return result

def read_latest_inbox(tool_context: ToolContext, top: int = 10) -> List[Dict[str, Any]]:
    """
    Tool: Returns latest emails (read + unread) (top N) from Inbox.
    """
    result = _graph.list_inbox_messages(top=top, unread_only=False)
    #tool_context.state["latest_email_list"] = result
    return result

def read_message_full(tool_context: ToolContext, message_id: str, prefer_text: bool = True) -> Dict[str, Any]:
    """
    Tool: Returns full message details including body.
    """
    result = _graph.get_message(message_id=message_id, prefer_text=prefer_text)
    tool_context.state["full_message"] = result
    return result

def mark_message_read(message_id: str) -> Dict[str, Any]:
    """
    Tool: Marks an email as read.
    """
    _graph.mark_as_read(message_id=message_id)
    return {"status": "ok", "message_id": message_id}
