import re
from google.adk.tools.tool_context import ToolContext

def validateEmailIfRMA(tool_context: ToolContext) -> bool:
    """Returns True if subject contains whole word 'RMA' (case-sensitive)."""
    
    full_message = tool_context.state.get("full_message")

    if not full_message:
        return False
    
    subject = full_message.get("subject", "")
    body = full_message.get("body", {}).get("content", "")

    print(f"DEBUG Subject: {subject}")
    print(f"DEBUG Body: {body}")

    # Case-sensitive whole-word match
    boolRMA = bool(re.search(r"\bRMA\b", subject))
    tool_context.state["boolRMA"] == boolRMA
    return boolRMA