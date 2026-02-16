from google.adk.agents import LlmAgent
from .sub_agents.email_agent.agent import email_agent
from .sub_agents.bigquery_agent.agent import bigquery_agent 

root_agent = LlmAgent(
    name="main_agent",
    model="gemini-2.5-flash",
    instruction="""
You are the Main Agent (orchestrator).

Workflow:
1. Use email_agent to retrieve and validate emails.
2. Pass structured email_records to bigquery_agent.
3. bigquery_agent prepares the data for persistence.
""",
    sub_agents=[
        email_agent,
        bigquery_agent,
    ],
)
