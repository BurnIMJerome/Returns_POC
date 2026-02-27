from unittest import result
import copy 
from google.adk.agents import LlmAgent
import google.auth
from pydantic import BaseModel, Field
from typing import Dict, Optional, Literal, Union, Any
from datetime import datetime
from .instruction import validation_agent_instruction
from google.adk.tools.tool_context   import ToolContext 
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse

from ...tools.validation_tools import (
    validateEmailIfRMA,
)

# Guardrails import
from ...guardrails import (
    before_model_guard,
)

# -bigquery reference start
from google.adk.tools.bigquery import BigQueryCredentialsConfig
from google.adk.tools.bigquery import BigQueryToolset
from google.adk.tools.bigquery.config import BigQueryToolConfig
from google.adk.tools.bigquery.config import WriteMode
from google.genai import types
tool_config = BigQueryToolConfig(write_mode=WriteMode.ALLOWED)

application_default_credentials, _ = google.auth.default()
credentials_config = BigQueryCredentialsConfig(
    credentials=application_default_credentials
)

# Instantiate a BigQuery toolset
bigquery_toolset = BigQueryToolset(
     credentials_config=credentials_config,bigquery_tool_config=tool_config
)

# -----------------------------
# Output Schemas
# -----------------------------

class NotRMAOutput(BaseModel):
    status: Literal["not_rma"] = Field(description="Classification result.")
    message: str = Field(description="User-friendly explanation.")
    reason: str = Field(description="Short reason based on email content.")
    detected_category: Literal[
        "newsletter",
        "security_digest",
        "marketing",
        "system_notification",
        "other"
    ]
    next_step: str = Field(description="What the user should do next.")


class ValidationErrorOutput(BaseModel):
    status: Literal["error"] = "error"
    error_type: Literal["validation_error"] = "validation_error"
    message: str
    missing_fields: list[str]
    next_step: str

class InsertMetadata(BaseModel):
        insert_status: Optional[Literal["inserted", "failed", "skipped"]] = Field(
        default=None,
        description="Insert outcome. 'skipped' for not_rma or validation_error."
    )
        inserted_row_id: Optional[str] = Field(
        default=None,
        description="Row id/insert id if available from the insert tool."
    )
        insert_error: Optional[str] = Field(
        default=None,
        description="Insert error details if insert failed."
    )

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
    insert_metadata: Optional[InsertMetadata] = Field(
        default=None,
        description="Metadata about the insert operation."
    )

class OutputSchema(BaseModel):
    """
    Validation agent output wrapper.
    """
    result: Union[
        NotRMAOutput,
        ValidationErrorOutput,
        RMAOutput
    ]

# -----------------------------
# Validation Agent
# -----------------------------

def after_model_callback_def(callback_context: CallbackContext, llm_response: LlmResponse
) -> Optional[LlmResponse]:
    """
    After the model produces output, this callback just save the response in state.
    """
       # Validate structure safely
    if (
        not llm_response
        or not llm_response.content
        or not llm_response.content.parts
        or len(llm_response.content.parts) == 0
        or not hasattr(llm_response.content.parts[0], "text")
        or not llm_response.content.parts[0].text
        or not llm_response.content.parts[0].text.strip()
    ):
         print("\n[AFTER MODEL] LLM response is empty or malformed. No modifications.")
         return llm_response
    
    modified_llm_response = copy.deepcopy(llm_response)

    # Assuming the main text is in the first part
    original_text = modified_llm_response.content.parts[0].text
    current_text = original_text  # Start with original for modification

    print(f"\n[AFTER MODEL] Original LLM response: '{original_text}'")
    callback_context.state["validation_result"] = original_text
    
    return None

validation_agent = LlmAgent(
    name="validation_agent",
    model="gemini-2.5-flash",
    output_schema=OutputSchema,
    instruction=validation_agent_instruction,
    tools=[validateEmailIfRMA, bigquery_toolset],
    after_model_callback=after_model_callback_def,
    before_model_callback=before_model_guard, # Guardrails call
)
