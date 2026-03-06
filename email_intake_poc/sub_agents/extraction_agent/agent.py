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
from .instruction import extraction_agent_instruction
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


class RMAOutput(BaseModel):
    Customer_ID: str = Field(
        description="Customer identifier extracted from selected_email body."
    )
    Order_Number: Optional[str] = Field(
        default=None,
        description="Sales order number if present in selected_email."
    )
    Invoice_Number: Optional[str] = Field(
        default=None,
        description="Invoice number if present in selected_email."
    )
    RMA_Type: Optional[Literal["Return", "Repair", "Replacement", "Credit"]] = Field(
        default=None,
        description="Type of RMA request if explicitly stated."
    )
    Reason_Code: Optional[str] = Field(
        default=None,
        description="Derived reason code if clearly supported by the email text; otherwise null."
    )
    Status: Literal["Pending"] = Field(
        default="Pending",
        description="Always Pending for new intake."
    )
    Priority: Optional[Literal["High", "Medium", "Low"]] = Field(
        default=None,
        description="Derived from explicit urgency indicators; otherwise null."
    )
    Created_Date: datetime = Field(
        description="Email sent datetime (from selected_email metadata)."
    )
    Approved_Date: Optional[datetime] = Field(
        default=None,
        description="Approval datetime only if explicitly stated; otherwise null."
    )
    Closed_Date: Optional[datetime] = Field(
        default=None,
        description="Closure datetime only if explicitly stated; otherwise null."
    )
    Created_By: Literal["agentic-ai"] = Field(
        default="agentic-ai",
        description="System-defined creator identifier."
    )
    Source_Channel: Literal["Email"] = Field(
        default="Email",
        description="System-defined source channel."
    )
    Issue_Description: Optional[str] = Field(
        default=None,
        description="Derived issue description if clearly supported by the email text; otherwise null."
    )
    # Validation and ServiceNow metadata
    validation_status: Optional[Literal["passed", "failed", "skipped"]] = Field(
        default=None,
        description="Result of business validation: passed/failed/skipped"
    )
    case_status: Optional[Literal["created", "failed", "not_created"]] = Field(
        default=None,
        description="ServiceNow case creation status: created/failed/not_created"
    )
    case_sys_id: Optional[str] = Field(
        default=None,
        description="ServiceNow sys_id if created"
    )
    case_number: Optional[str] = Field(
        default=None,
        description="ServiceNow case number if created"
    )
    case_error: Optional[str] = Field(
        default=None,
        description="ServiceNow error string if creation failed"
    )


# -----------------------------
# Extraction Agent
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
    callback_context.state["extraction_result_raw"] = original_text

    # Try to parse JSON to a dict for reliable downstream logic
    parsed = None
    try:
        parsed = json.loads(original_text)
    except Exception:
        # If model sometimes wraps JSON with extra whitespace, you can try minimal cleanup here
        parsed = None

    if parsed is not None:
        callback_context.state["extraction_result"] = parsed
    else:
        # fallback: keep raw string in the same key if you prefer
        callback_context.state["extraction_result"] = original_text

    return llm_response




extraction_agent = LlmAgent(
    name="extraction_agent",
    model="gemini-2.5-flash",
    output_schema=RMAOutput,
    instruction=extraction_agent_instruction,
    after_model_callback=after_model_callback_def,
    before_model_callback=before_model_guard, 
    
)
