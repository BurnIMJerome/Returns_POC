from __future__ import annotations
from typing import Any, Dict, List
from unittest import result


from ..clients.graph_client import GraphMailClient

from google.adk.tools.tool_context  import ToolContext 
import requests
import logging

_graph = GraphMailClient()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rpa_tool")

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

def submit_rma(customer_id):
    """
    Submit an RMA by making a POST request to the Power Automate API.

    Args:
        customer_id (str): The Customer_ID to include in the payload.

    Returns:
        dict: The API response and status code.
    """
    url = "https://320da500b1c942b5821790fc274f46.a4.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/2dc274d1b3834530a1ef5750fd35339b/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=5WqomQ1HEcScO7CWlm3P_oYzHysocd-xzsjrU87pAsM"

    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "Customer_ID": customer_id
    }

    try:
        logger.info("Sending POST request to API.")
        logger.info(f"URL: {url}")
        logger.info(f"Payload: {payload}")
        response = requests.post(url, json=payload, headers=headers)
        logger.info(f"Response Status Code: {response.status_code}")
        logger.info(f"Response Body: {response.text}")
        return {"status_code": response.status_code, "response": response.json()}
    except requests.exceptions.RequestException as e:
        logger.error("Error occurred during API call.")
        logger.error(f"Error details: {e}")
        return {"error": str(e)}
