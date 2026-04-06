from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool
from email_intake_poc.sub_agents.validation_agent import validation_agent
from email_intake_poc.sub_agents.extraction_agent import extraction_agent
from email_intake_poc.sub_agents.bigquery_insert_agent import bigquery_insert_agent
from email_intake_poc.sub_agents.servicenow_agent import servicenow_agent
from google.adk.agents.callback_context import CallbackContext
from typing import Optional
from .instruction import email_agent_instruction
from google.adk.models import LlmResponse
from ...tools.email_tools import (
    read_unread_inbox,
    read_latest_inbox,
    read_message_full,
)
# Guardrails import
from ...guardrails import (
    before_model_guard,
)

def init_email_agent_state(callback_context: CallbackContext):
    state = callback_context.session.state

    state.setdefault("validation_result", {})
    state.setdefault("extraction_result", {})
    state.setdefault("bigquery_insert_result", {})
    state.setdefault("servicenow_result", {})
    state.setdefault("selected_email_number", None)

    return None

email_agent = LlmAgent(
    name="email_agent",
    model="gemini-2.5-flash",
    instruction=email_agent_instruction,
    before_agent_callback=init_email_agent_state,
    tools=[
        AgentTool(validation_agent),
        AgentTool(extraction_agent),
        AgentTool(bigquery_insert_agent),
        AgentTool(servicenow_agent),
        read_unread_inbox,
        read_latest_inbox,
        read_message_full,
      
    ],
   

    
)
