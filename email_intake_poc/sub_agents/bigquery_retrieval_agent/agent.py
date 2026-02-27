from google.adk.agents.llm_agent import Agent
from .instruction import bigquery_retrieval_agent_instruction
from google.adk.tools.bigquery import (BigQueryToolset, BigQueryCredentialsConfig)
from google.adk.tools.bigquery.config import (BigQueryToolConfig, WriteMode)
import google.auth

# Guardrails import
from ...guardrails import (
    before_model_guard,
)

# 1. Credentials
application_default_credentials, _ = google.auth.default()
credentials_config = BigQueryCredentialsConfig(
    credentials=application_default_credentials
)

# 2. Safety Setting for Retrieval
# WriteMode.BLOCKED ensures the agent can only SELECT, not INSERT/UPDATE
retrieval_tool_config = BigQueryToolConfig(write_mode=WriteMode.BLOCKED)

# 3. Instantiate the Toolset
bigquery_retrieval_toolset = BigQueryToolset(
    credentials_config=credentials_config, 
    bigquery_tool_config=retrieval_tool_config
)

bigquery_retrieval_agent = Agent(
    model="gemini-2.5-flash",
    name="bigquery_retrieval_agent",
    description="A helpful assistant for retrieving information from BigQuery based on a single or multiple selected search criteria.",
    instruction=bigquery_retrieval_agent_instruction,
    tools=[bigquery_retrieval_toolset],
    output_key="bigquery_retrieval_result",
    before_model_callback=before_model_guard, # Guardrails call
)
