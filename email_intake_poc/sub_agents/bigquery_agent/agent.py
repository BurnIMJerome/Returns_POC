from google.adk.agents import LlmAgent
from .instruction import bigquery_agent_instruction
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from ...tools.email_tools import (
    read_message_full,
    mark_message_read
)



class OutputSchema(BaseModel):
  RMA_ID: Optional[str] = Field(
    default=None,
    description="RMA ID extracted directly from the email if explicitly provided (e.g., RMA-100245). Must NOT be generated. Set to null if not present in the email."
)

Customer_ID: str = Field(
    description="Customer identifier explicitly stated in the email. Must not be inferred or fabricated."
)

Order_Number: Optional[str] = Field(
    default=None,
    description="Sales order number extracted only if clearly mentioned in the email. Otherwise null."
)

Invoice_Number: Optional[str] = Field(
    default=None,
    description="Invoice number extracted only if explicitly present in the email. Otherwise null."
)

RMA_Type: Optional[Literal["Return", "Repair", "Replacement", "Credit"]] = Field(
    default=None,
    description="Type of RMA request derived strictly from explicit context in the email (e.g., 'return', 'replacement'). Set to null if unclear."
)

Reason_Code: Optional[str] = Field(
    default=None,
    description="Reason code derived from the issue description in the email using a predefined mapping (e.g., DF for Defective). Must not be guessed. Set to null if no clear mapping exists."
)

Status: Literal["Pending"] = Field(
    default="Pending",
    description="RMA status. Always set to 'Pending' at initial intake regardless of email content."
)

Priority: Optional[Literal["High", "Medium", "Low"]] = Field(
    default=None,
    description="Priority level derived only if urgency indicators are explicitly stated in the email (e.g., 'urgent', 'ASAP'). Otherwise null."
)

Created_Date: datetime = Field(
    description="Email sent datetime taken directly from email metadata in ISO 8601 format."
)

Approved_Date: Optional[datetime] = Field(
    default=None,
    description="Approval datetime only if explicitly stated in the email. Otherwise null."
)

Closed_Date: Optional[datetime] = Field(
    default=None,
    description="Closure datetime only if explicitly stated in the email. Otherwise null."
)

Created_By: Literal["agentic-ai"] = Field(
    default="agentic-ai",
    description="System-generated value identifying the agent as the creator. Not extracted from the email."
)

Source_Channel: Literal["Email"] = Field(
    default="Email",
    description="Indicates that the source of this RMA request is Email. System-defined value."
)



bigquery_agent = LlmAgent(
    name="bigquery_agent",
    model="gemini-2.5-flash",
    instruction=bigquery_agent_instruction,
    output_schema=OutputSchema
    
)
