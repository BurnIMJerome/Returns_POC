from google.adk.agents import LlmAgent
from .instruction import email_agent_instruction
from ...tools.email_tools import (
    read_unread_inbox,
    read_latest_inbox,
    read_message_full,
)

email_agent = LlmAgent(
    name="email_agent",
    model="gemini-2.5-flash",
    instruction=email_agent_instruction,
    tools=[
        read_unread_inbox,
        read_latest_inbox,
        read_message_full,
    ],
    output_key="email_records",
    
)
