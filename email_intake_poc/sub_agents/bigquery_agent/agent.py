from google.adk.agents import LlmAgent
import google.auth

from email_intake_poc.sub_agents.validation_agent.agent import ValidationAgent
from .instruction import bigquery_agent_instruction
from pydantic import BaseModel, Field
from typing import Optional, Literal, Union
from datetime import datetime
from ...tools.email_tools import (
    read_message_full,
    mark_message_read
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

class OutputSchema(BaseModel):
    """Top-level wrapper model. LlmAgent expects a single BaseModel subclass for output_schema.

    The actual result is stored in the `result` field which can be either NotRMAOutput or RMAOutput.
    """
    result: Union[NotRMAOutput, RMAOutput]


bigquery_agent = LlmAgent(
    name="bigquery_agent",
    model="gemini-2.5-flash",
    output_schema=OutputSchema,
    output_key="bigquery_result",
    instruction=bigquery_agent_instruction,
   
    tools=[bigquery_toolset],
    ##tools=[insert_rma_header_to_bigquery],

)


def process_rma(bigquery_result, bigquery_client):
    validation_agent = ValidationAgent()

    # Step 0: Call validation agent first
    validation_response = validation_agent.validate(bigquery_result)

    if validation_response:
        # Validation failed → return JSON error
        return validation_response

    # Step 1: NOT_RMA check
    if bigquery_result.get("status") == "not_rma":
        return bigquery_result

    # Step 2: Normalization
    rma = bigquery_result
    if rma.get("RMA_ID") and len(rma["RMA_ID"]) > 20:
        rma["RMA_ID"] = rma["RMA_ID"][:20]

    rma["Status"] = "Pending"
    rma["Created_By"] = "agentic-ai"
    rma["Source_Channel"] = "Email"
    rma["Approved_Date"] = rma.get("Approved_Date")
    rma["Closed_Date"] = rma.get("Closed_Date")

    # Step 3: Insert into BigQuery
    try:
        bigquery_client.insert_row(
            project="agentic-ai-poc-486504",
            dataset="RMA",
            table="RMA_Header",
            row=rma
        )
    except Exception as e:
        return {
            "status": "error",
            "error_type": "bigquery_insert_error",
            "message": "Failed to insert RMA record into BigQuery.",
            "details": str(e),
            "next_step": "Verify BigQuery permissions, quota project configuration, and table schema."
        }

    # Step 4: Success
    return f"RMA Record Successfully Created with RMA_ID: {rma.get('RMA_ID', 'NULL')}"