from ...config import settings
from unittest import result
import copy 
from google.adk.agents import LlmAgent
from google.adk.agents import callback_context
from google.adk.agents import callback_context
import google.auth
from pydantic import BaseModel, Field
from typing import Dict, Optional, Literal, Union, Any
from datetime import datetime
from .instruction import validation_agent_instruction
from google.adk.tools.tool_context   import ToolContext 
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse
import json
# Guardrails import
from ...guardrails import (
    before_model_guard,
)
# Import tools and the actual bigquery_insert_agent
from ...tools.validation_tools import validateEmailIfRMA
from ...tools.servicenow_tools import (
    snow_create_record,
    snow_get_record,
    snow_query_records,
    snow_update_record,
    snow_delete_record,
)
from google.adk.tools.bigquery import BigQueryToolset, BigQueryCredentialsConfig
from google.adk.tools.bigquery.config import BigQueryToolConfig, WriteMode
import google.auth

# -----------------------------
# Output Schemas
# -----------------------------




# --- BigQueryToolset setup for direct use ---
application_default_credentials, _ = google.auth.default()
credentials_config = BigQueryCredentialsConfig(credentials=application_default_credentials)
tool_config = BigQueryToolConfig(
    write_mode=WriteMode.ALLOWED,
    location=getattr(settings, "GOOGLE_CLOUD_LOCATION", "asia-southeast1")
)
bigquery_toolset = BigQueryToolset(credentials_config=credentials_config, bigquery_tool_config=tool_config)

validation_agent = LlmAgent(
    name="validation_agent",
    model="gemini-2.5-flash",
    #output_schema=OutputSchema,
    instruction=validation_agent_instruction,
    tools=[
        #validateEmailIfRMA,  # Reactivated the validateEmailIfRMA tool
        bigquery_toolset,
        snow_create_record,
        snow_get_record,
        snow_query_records
    ],
    #after_model_callback=after_model_callback_def,
    before_model_callback=before_model_guard, # Guardrails call
)