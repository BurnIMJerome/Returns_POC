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

Routing Rules:

1) If user asks to list emails:
   → Call email_agent.

2) If user says "process N":
   → Identify selected email from email_records.
   → Call read_message_full tool directly.
   → Then call bigquery_agent with the full email data.

Important:
- Do not stop after fetching full email.
- Always call bigquery_agent after full content is retrieved for processing.
""",
    tools=[read_message_full],  
    sub_agents=[email_agent, bigquery_agent],
)
