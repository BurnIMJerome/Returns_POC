from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool
from email_intake_poc.sub_agents.validation_agent import validation_agent
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
    tools=[AgentTool(validation_agent),
        read_unread_inbox,
        read_latest_inbox,
        read_message_full,
      
    ],
    #sub_agents=[validation_agent]

    
)
