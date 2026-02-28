import os
from google.adk.agents import LlmAgent
import google.auth

from .instruction import bigquery_agent_instruction
from pydantic import BaseModel, Field
from typing import Optional, Literal, Union
from datetime import datetime
from ...tools.email_tools import (
    read_message_full,
    mark_message_read
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

# Pass region/location as a string from settings only (no fallback)


# Only pass location (region) in tool_config
tool_config = BigQueryToolConfig(
    write_mode=WriteMode.ALLOWED,
    location=getattr(settings, "GOOGLE_CLOUD_LOCATION", None)
)

application_default_credentials, _ = google.auth.default()
credentials_config = BigQueryCredentialsConfig(
    credentials=application_default_credentials
)

# Instantiate a BigQuery toolset
bigquery_toolset = BigQueryToolset(
    credentials_config=credentials_config, bigquery_tool_config=tool_config
)
##from .bigquery_Tools.rma_bigquery_insert_tool import ( insert_rma_header_to_bigquery)
# -bigquery reference end


class NotRMAOutput(BaseModel):
    status: Literal["not_rma"] = Field(description="Classification result.")
    message: str = Field(description="User-friendly explanation.")
    reason: str = Field(description="Short reason based on email content.")
    detected_category: Literal["newsletter", "security_digest", "marketing", "system_notification", "other"]
    next_step: str = Field(description="What the user should do next.")


class RMAOutput(BaseModel):
    Customer_ID: str = Field(description="Customer identifier extracted from selected_email body.")
    Order_Number: Optional[str] = Field(default=None, description="Sales order number if present in selected_email.")
    Invoice_Number: Optional[str] = Field(default=None, description="Invoice number if present in selected_email.")
    RMA_Type: Optional[Literal["Return", "Repair", "Replacement", "Credit"]] = Field(default=None, description="Type of RMA request if explicitly stated.")
    Reason_Code: Optional[str] = Field(default=None, description="Derived reason code if clearly supported by the email text; otherwise null.")
    Status: Literal["Pending"] = Field(default="Pending", description="Always Pending for new intake.")
    Priority: Optional[Literal["High", "Medium", "Low"]] = Field(default=None, description="Derived from explicit urgency indicators; otherwise null.")
    Created_Date: datetime = Field(description="Email sent datetime (from selected_email metadata).")
    Approved_Date: Optional[datetime] = Field(default=None, description="Approval datetime only if explicitly stated; otherwise null.")
    Closed_Date: Optional[datetime] = Field(default=None, description="Closure datetime only if explicitly stated; otherwise null.")
    Created_By: Literal["agentic-ai"] = Field(default="agentic-ai", description="System-defined creator identifier.")
    Source_Channel: Literal["Email"] = Field(default="Email", description="System-defined source channel.")
    RMA_ID: Optional[str] = Field(default=None, description="Auto-generated RMA identifier.")

    def ensure_rma_id(self):
        if not self.RMA_ID or self.RMA_ID.strip().lower() == "null":
            # Generate RMA_ID: first 2 chars of Customer_ID + first 2 of Order_Number + MMDDhhmmss
            from datetime import datetime as dt
            cid = (self.Customer_ID or "XX")[:2]
            oid = (self.Order_Number or "YY")[:2]
            now = dt.now().strftime("%m%d%H%M%S")
            self.RMA_ID = f"{cid}{oid}{now}"
            if len(self.RMA_ID) > 20:
                self.RMA_ID = self.RMA_ID[:20]
        return self.RMA_ID

class OutputSchema(BaseModel):
    """Top-level wrapper model. LlmAgent expects a single BaseModel subclass for output_schema.

    The actual result is stored in the `result` field which can be either NotRMAOutput or RMAOutput.
    """
    result: Union[NotRMAOutput, RMAOutput]



# Patch the agent to auto-generate RMA_ID before insert
from google.adk.tools.tool_context import ToolContext
from google.adk.models import LlmResponse
import copy

def after_model_callback_def(callback_context: ToolContext, llm_response: LlmResponse):
    # Minimal, robust: only check required fields, pass through only what was extracted
    if not llm_response or not llm_response.content or not llm_response.content.parts:
        empty_json = json.dumps({"result": {}})
        llm_response = copy.deepcopy(llm_response)
        part = llm_response.content.parts[0] if llm_response.content.parts else None
        if part and hasattr(part, 'text'):
            part.text = empty_json
        return llm_response
    part = llm_response.content.parts[0]
    if hasattr(part, 'function_call') or hasattr(part, 'data'):
        return llm_response
    text = part.text
    minimal_valid = json.dumps({"result": {"status": "not_rma", "message": "No valid output", "reason": "empty or invalid LLM response", "detected_category": "other", "next_step": "Check input and try again."}})
    if not text or not text.strip():
        llm_response = copy.deepcopy(llm_response)
        if hasattr(part, 'text'):
            part.text = minimal_valid
        return llm_response
    try:
        data = json.loads(text)
        result = data.get("result")
        missing_fields = []
        if not result or not isinstance(result, dict):
            missing_fields = ["Customer_ID", "RMA_Type", "Order_Number or Invoice_Number"]
        else:
            if not result.get("Customer_ID"):
                missing_fields.append("Customer_ID")
            if not result.get("RMA_Type"):
                missing_fields.append("RMA_Type")
            if not (result.get("Order_Number") or result.get("Invoice_Number")):
                missing_fields.append("Order_Number or Invoice_Number")
        if missing_fields:
            error_obj = {
                "result": {
                    "status": "error",
                    "error_type": "validation_error",
                    "message": "Required RMA identifiers are missing.",
                    "missing_fields": missing_fields,
                    "next_step": "Ensure Customer_ID, RMA_Type, and either Order_Number or Invoice_Number are present before retrying."
                }
            }
            llm_response = copy.deepcopy(llm_response)
            if hasattr(part, 'text'):
                part.text = json.dumps(error_obj)
            return llm_response
        # Only include fields that exist in the BigQuery schema
        allowed_fields = [
            "RMA_ID", "Customer_ID", "Order_Number", "Invoice_Number", "RMA_Type", "Reason_Code", "Status", "Priority", "Created_Date", "Approved_Date", "Closed_Date", "Created_By", "Source_Channel"
        ]
        filtered_result = {k: v for k, v in result.items() if k in allowed_fields}
        data["result"] = filtered_result
        # Debug print of the payload being sent to BigQuery
        import json
        print("DEBUG: BigQuery payload:", json.dumps(filtered_result, indent=2))
        llm_response = copy.deepcopy(llm_response)
        if hasattr(llm_response.content.parts[0], 'text'):
            llm_response.content.parts[0].text = json.dumps(data)
        return llm_response
    except Exception:
        llm_response = copy.deepcopy(llm_response)
        if hasattr(part, 'text'):
            part.text = minimal_valid
        return llm_response

bigquery_insert_agent = LlmAgent(
    name="bigquery_agent",
    model="gemini-2.5-flash",
    output_schema=OutputSchema,
    output_key="bigquery_result",
    instruction=bigquery_agent_instruction,
    tools=[bigquery_toolset],
    after_model_callback=after_model_callback_def,
)