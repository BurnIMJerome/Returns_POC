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
from .instruction import servicenow_agent_instruction
from google.adk.tools.tool_context   import ToolContext 
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse
import json
# Guardrails import
from ...guardrails import (
    before_model_guard,
)
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

class ServiceNowOutput(BaseModel):
    """
    Output schema for ServiceNow incident creation.
    """

    case_status: Literal["created", "failed", "not_created"] = Field(
        description="Result of the ServiceNow incident creation."
    )

    case_sys_id: Optional[str] = Field(
        default=None,
        description="ServiceNow sys_id of the created incident if successful."
    )

    case_number: Optional[str] = Field(
        default=None,
        description="ServiceNow incident number if created."
    )

    case_error: Optional[str] = Field(
        default=None,
        description="Error message if case creation failed or was skipped."
    )


# --- BigQueryToolset setup for direct use ---
application_default_credentials, _ = google.auth.default()
credentials_config = BigQueryCredentialsConfig(credentials=application_default_credentials)
tool_config = BigQueryToolConfig(
    write_mode=WriteMode.ALLOWED,
    
)
bigquery_toolset = BigQueryToolset(credentials_config=credentials_config, bigquery_tool_config=tool_config)

servicenow_agent = LlmAgent(
    name="servicenow_agent",
    model="gemini-2.5-flash",
    output_schema=ServiceNowOutput,
    instruction=servicenow_agent_instruction,
    tools=[
        snow_create_record,
        snow_get_record,
        snow_query_records
    ],
    
)
