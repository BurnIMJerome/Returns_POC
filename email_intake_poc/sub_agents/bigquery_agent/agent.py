from google.adk.agents import LlmAgent
from .instruction import bigquery_agent_instruction
from ...tools.email_tools import (
    read_message_full,
    mark_message_read
)

bigquery_agent = LlmAgent(
    name="bigquery_agent",
    model="gemini-2.5-flash",
    instruction=bigquery_agent_instruction,
   
    
)
