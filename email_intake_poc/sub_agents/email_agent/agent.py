from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool
from email_intake_poc.sub_agents.validation_agent import validation_agent
from email_intake_poc.sub_agents.extraction_agent import extraction_agent
from email_intake_poc.sub_agents.bigquery_insert_agent import bigquery_insert_agent
from email_intake_poc.sub_agents.servicenow_agent import servicenow_agent
from .instruction import email_agent_instruction
from ...tools.email_tools import (
    read_unread_inbox,
    read_latest_inbox,
    read_message_full,
)
# Guardrails import
from ...guardrails import (
    before_model_guard,
)

email_agent = LlmAgent(
    name="email_agent",
    model="gemini-2.5-flash",
    instruction=email_agent_instruction,
    tools=[
        AgentTool(validation_agent),
        AgentTool(extraction_agent),
        AgentTool(bigquery_insert_agent),
        AgentTool(servicenow_agent),
        read_unread_inbox,
        read_latest_inbox,
        read_message_full,
      
    ],
    before_model_callback=before_model_guard, # Gaurdrails call  

    
)
