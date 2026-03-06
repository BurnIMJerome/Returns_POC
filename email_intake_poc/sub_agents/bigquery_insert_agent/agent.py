import os
from google.adk.agents import LlmAgent
import google.auth

from .instruction import bigquery_agent_instruction
from pydantic import BaseModel, Field
from typing import Optional, Literal, Union
from datetime import datetime
from google.adk.tools.tool_context   import ToolContext 
from google.adk.agents.callback_context import CallbackContext
# Guardrails import
from ...guardrails import (
    before_model_guard,
)
import json
# -bigquery reference start
from google.adk.tools.bigquery import BigQueryCredentialsConfig
from google.adk.tools.bigquery import BigQueryToolset
from google.adk.tools.bigquery.config import BigQueryToolConfig
from google.adk.tools.bigquery.config import WriteMode
from google.genai import types
from ...config import settings

# Debug print after settings is loaded (dotenv already loaded)
print("DEBUG: BIGQUERY_PROJECT from settings:", settings.BIGQUERY_PROJECT)


# --- BigQueryToolset setup for direct use ---
application_default_credentials, _ = google.auth.default()
credentials_config = BigQueryCredentialsConfig(credentials=application_default_credentials)
tool_config = BigQueryToolConfig(
    write_mode=WriteMode.ALLOWED,
    

)
bigquery_toolset = BigQueryToolset(credentials_config=credentials_config, bigquery_tool_config=tool_config)


class BigQueryInsertOutput(BaseModel):
    status: Literal["inserted", "failed", "skipped"] = Field(
        description="Result of the BigQuery insert operation."
    )
    affected_rows: int = Field(
        description="Number of rows inserted. Must be 1 on success."
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if insert failed, otherwise null."
    )




# Patch the agent to auto-generate RMA_ID before insert
from google.adk.tools.tool_context import ToolContext
from google.adk.models import LlmResponse
import copy

def after_model_callback_def(
    callback_context: CallbackContext,
    llm_response: LlmResponse
) -> Optional[LlmResponse]:

    def extract_all_text(resp: LlmResponse) -> Optional[str]:
        if not resp or not getattr(resp, "content", None):
            return None
        parts = getattr(resp.content, "parts", None) or []
        texts = []
        for p in parts:
            t = getattr(p, "text", None)
            if t and t.strip():
                texts.append(t.strip())
        return "\n".join(texts).strip() if texts else None

    original_text = extract_all_text(llm_response)
    if not original_text:
        print("\n[AFTER MODEL] LLM response is empty or malformed.")
        return llm_response

    # Always keep raw text for debugging/auditing
    callback_context.state["bigquery_insert_result_raw"] = original_text

    # Try to parse JSON to a dict for reliable downstream logic
    parsed = None
    try:
        parsed = json.loads(original_text)
    except Exception:
        # If model sometimes wraps JSON with extra whitespace, you can try minimal cleanup here
        parsed = None

    if parsed is not None:
        callback_context.state["bigquery_insert_result"] = parsed
    else:
        # fallback: keep raw string in the same key if you prefer
        callback_context.state["bigquery_insert_result"] = original_text

    return llm_response

bigquery_insert_agent = LlmAgent(
    name="bigquery_agent",
    model="gemini-2.5-flash",
    output_schema=BigQueryInsertOutput,
    output_key="bigquery_result",
    instruction=bigquery_agent_instruction, 
    tools=[bigquery_toolset],
    after_model_callback=after_model_callback_def,
)