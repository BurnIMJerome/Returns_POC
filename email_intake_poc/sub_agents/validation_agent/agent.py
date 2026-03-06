from ...config import settings
from unittest import result
import copy 
from google.adk.agents import LlmAgent
from google.adk.agents import callback_context
from google.adk.agents import callback_context
import google.auth
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Literal, Union, Any
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

class ValidationOutput(BaseModel):
    status: Literal["rma", "not_rma"] = Field(description="Classification result.")
    reason: str = Field(description="Short reason based on subject/body evidence.")
    signals: List[str] = Field(default_factory=list, description="Evidence strings found in the email.")


# -----------------------------
# Validation Agent
# -----------------------------

import json
from typing import Optional
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse

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
    callback_context.state["validation_result_raw"] = original_text

    # Try to parse JSON to a dict for reliable downstream logic
    parsed = None
    try:
        parsed = json.loads(original_text)
    except Exception:
        # If model sometimes wraps JSON with extra whitespace, you can try minimal cleanup here
        parsed = None

    if parsed is not None:
        callback_context.state["validation_result"] = parsed
    else:
        # fallback: keep raw string in the same key if you prefer
        callback_context.state["validation_result"] = original_text

    return llm_response


validation_agent = LlmAgent(
    name="validation_agent",
    model="gemini-2.5-flash",
    output_schema= ValidationOutput,
    instruction=validation_agent_instruction,
    after_model_callback=after_model_callback_def,
    before_model_callback=before_model_guard, 
    
)
