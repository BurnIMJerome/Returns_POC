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
    RMA_ID: Optional[str] = Field(
        default=None,
        description="Extracted from email if explicitly present; otherwise null. Max 20 chars."
    )
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
