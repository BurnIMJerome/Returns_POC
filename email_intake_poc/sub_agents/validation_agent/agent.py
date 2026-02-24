from google.adk.agents import LlmAgent
from pydantic import BaseModel, Field
from typing import Optional, Literal, Union
from datetime import datetime

from .instruction import validation_agent_instruction


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

validation_agent = LlmAgent(
    name="validation_agent",
    model="gemini-2.5-flash",
    instruction=validation_agent_instruction,
    output_schema=OutputSchema,
    output_key="validation_result",
    tools=[]  # ✅ NO TOOLS — validation only
)

__all__ = ["validation_agent"]