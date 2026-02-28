from google.adk.agents.llm_agent import Agent
from ...config import settings
from .instruction import bigquery_retrieval_agent_instruction
from google.adk.tools.bigquery import (BigQueryToolset, BigQueryCredentialsConfig)
from google.adk.tools.bigquery.config import (BigQueryToolConfig, WriteMode)
import google.auth


# 1. Credentials
application_default_credentials, _ = google.auth.default()
credentials_config = BigQueryCredentialsConfig(
    credentials=application_default_credentials
)

# 1a. Reference BigQuery config values for clarity
BIGQUERY_PROJECT = settings.BIGQUERY_PROJECT
BIGQUERY_DATASET = settings.BIGQUERY_DATASET
BIGQUERY_TABLE = settings.BIGQUERY_TABLE


# Example: build full table reference if needed
BIGQUERY_TABLE_REF = f"{BIGQUERY_PROJECT}.{BIGQUERY_DATASET}.{BIGQUERY_TABLE}"

# Debug print to confirm config values before any query
import logging
logging.basicConfig(level=logging.INFO)
logging.info(f"[BigQuery Config] Project: {BIGQUERY_PROJECT}, Dataset: {BIGQUERY_DATASET}, Table: {BIGQUERY_TABLE}")

# 2. Safety Setting for Retrieval
# WriteMode.BLOCKED ensures the agent can only SELECT, not INSERT/UPDATE
retrieval_tool_config = BigQueryToolConfig(write_mode=WriteMode.BLOCKED)


# 3. Instantiate the Toolset with error logging wrapper
import logging
from google.adk.tools.bigquery import BigQueryToolset as _BigQueryToolset

class LoggingBigQueryToolset(_BigQueryToolset):
    def run(self, *args, **kwargs):
        try:
            return super().run(*args, **kwargs)
        except Exception as e:
            logging.error(f"[BigQuery Retrieval ERROR] {type(e).__name__}: {e}", exc_info=True)
            raise

bigquery_retrieval_toolset = LoggingBigQueryToolset(
    credentials_config=credentials_config,
    bigquery_tool_config=retrieval_tool_config
)

bigquery_retrieval_agent = Agent(
    model="gemini-2.5-flash",
    name="bigquery_retrieval_agent",
    description="A helpful assistant for retrieving information from BigQuery based on a single or multiple selected search criteria.",
    instruction=bigquery_retrieval_agent_instruction,
    tools=[bigquery_retrieval_toolset],
    output_key="bigquery_retrieval_result"
)
