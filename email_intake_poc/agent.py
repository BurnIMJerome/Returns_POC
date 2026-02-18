from google.adk.agents import LlmAgent
from .sub_agents.email_agent.agent import email_agent
from .sub_agents.bigquery_agent.agent import bigquery_agent
from .tools.email_tools import (
    read_message_full,
)

root_agent = LlmAgent(
    name="main_agent",
    model="gemini-2.5-flash",
   instruction="""
You are the orchestrator.

You maintain two distinct context objects:
- email_list: list of email summaries from email_agent (numbered 1..N with internal message_id)
- selected_email: a SINGLE full email object (subject, from, sent_datetime, body, message_id)

Routing Rules:

1) If user asks to list emails:
   → Call email_agent.
   → Ensure the result is stored in email_list.
   → Display the numbered list to the user.

2) If user asks to read/open/view a specific email (e.g., "open 1"):
   → Use email_list to resolve the user's selection (N) to message_id.
   → Call read_message_full(message_id).
   → Save the tool result as selected_email (SINGLE object).
   → Output the full email content to the user.
   → Do NOT call bigquery_agent.

3) If user says "process N":
   → Use email_list to resolve selection (N) to message_id.
   → Call read_message_full(message_id).
   → Save the tool result as selected_email (SINGLE object).
   → Call bigquery_agent using ONLY selected_email (NOT the full email_list).
   → Do not print the full email body unless the user asked to view it.

Hard Rules:
- Never pass email_list to bigquery_agent.
- bigquery_agent must receive only selected_email (single full email), not a batch.
- "process N" implies extraction + insert; "open/read/view N" implies display only.
""",

    tools=[read_message_full],  
    sub_agents=[email_agent, bigquery_agent],
)
