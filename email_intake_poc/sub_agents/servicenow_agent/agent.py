from __future__ import annotations

import json
from typing import Any, Dict, Optional, Literal

from pydantic import BaseModel, Field

from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse
from google.adk.tools.tool_context import ToolContext

from .instruction import servicenow_agent_instruction
from ...tools.servicenow_tools import snow_create_record


# -----------------------------
# Output Schema
# -----------------------------

class ServiceNowOutput(BaseModel):
    case_status: Literal["created", "failed", "not_created"] = Field(
        description="Result of the ServiceNow incident creation."
    )
    case_sys_id: Optional[str] = Field(
        default=None,
        description="ServiceNow sys_id if created."
    )
    case_number: Optional[str] = Field(
        default=None,
        description="ServiceNow incident number if created."
    )
    case_error: Optional[str] = Field(
        default=None,
        description="Error message if failed or skipped."
    )


# -----------------------------
# Deterministic helpers
# -----------------------------

def build_servicenow_fields(record: Dict[str, Any]) -> Dict[str, Any]:
    customer_id = record.get("Customer_ID") or "Unknown"
    order_number = record.get("Order_Number") or "N/A"
    invoice_number = record.get("Invoice_Number") or "N/A"
    rma_type = record.get("RMA_Type") or "N/A"
    reason_code = record.get("Reason_Code") or "N/A"
    priority = record.get("Priority") or "N/A"
    issue_description = record.get("Issue_Description") or "N/A"

    return {
        "short_description": f"RMA Request from Email - Customer {customer_id}",
        "description": (
            f"RMA_Type: {rma_type} | "
            f"Reason_Code: {reason_code} | "
            f"Order_Number: {order_number} | "
            f"Invoice_Number: {invoice_number} | "
            f"Priority: {priority}"
        ),
        "comments": (
            f"RMA received via email.\n"
            f"Customer_ID: {customer_id}\n"
            f"Order_Number: {order_number}\n"
            f"Invoice_Number: {invoice_number}\n"
            f"RMA_Type: {rma_type}\n"
            f"Reason_Code: {reason_code}\n"
            f"Priority: {priority}\n\n"
            f"Issue Description:\n{issue_description}"
        ),
    }


# -----------------------------
# Wrapper tool: read directly from state
# -----------------------------

def create_servicenow_incident_from_state(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Wrapper tool:
    - reads extraction_result from tool_context.state
    - checks validation_status
    - builds ServiceNow payload deterministically
    - calls snow_create_record exactly once
    - returns ServiceNowOutput-compatible dict
    """
    request = tool_context.state.get("extraction_result")

    if hasattr(request, "model_dump"):
        request = request.model_dump()

    if not isinstance(request, dict) or not request:
        return {
            "case_status": "failed",
            "case_sys_id": None,
            "case_number": None,
            "case_error": "missing_or_invalid_extraction_result",
        }

    if request.get("validation_status") != "passed":
        return {
            "case_status": "not_created",
            "case_sys_id": None,
            "case_number": None,
            "case_error": "validation_failed_missing_required_fields",
        }

    fields = build_servicenow_fields(request)
    print(f"[DEBUG] Deterministic ServiceNow payload: {fields}")

    try:
        response = snow_create_record(table="incident", fields=fields)
        print(f"[DEBUG] ServiceNow raw response: {response}")

        result = response.get("result", {}) if isinstance(response, dict) else {}
        sys_id = result.get("sys_id")
        number = result.get("number")

        if sys_id or number:
            return {
                "case_status": "created",
                "case_sys_id": sys_id,
                "case_number": number,
                "case_error": None,
            }

        return {
            "case_status": "failed",
            "case_sys_id": None,
            "case_number": None,
            "case_error": "snow_create_record returned no result or invalid result",
        }

    except Exception as e:
        return {
            "case_status": "failed",
            "case_sys_id": None,
            "case_number": None,
            "case_error": str(e),
        }


# -----------------------------
# Callback
# -----------------------------

def after_model_callback_def(
    callback_context: CallbackContext,
    llm_response: LlmResponse
) -> Optional[LlmResponse]:
    """
    Save final ServiceNow result to state.
    """

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
        print("[AFTER MODEL] ServiceNow agent returned empty response.")
        callback_context.state["servicenow_result_raw"] = ""
        callback_context.state["servicenow_result"] = {
            "case_status": "failed",
            "case_sys_id": None,
            "case_number": None,
            "case_error": "empty_model_response",
        }
        return llm_response

    callback_context.state["servicenow_result_raw"] = original_text

    try:
        parsed = json.loads(original_text)
        callback_context.state["servicenow_result"] = parsed
    except Exception as e:
        callback_context.state["servicenow_result"] = {
            "case_status": "failed",
            "case_sys_id": None,
            "case_number": None,
            "case_error": f"invalid_json_response: {str(e)}",
        }

    return llm_response


# -----------------------------
# Agent
# -----------------------------

servicenow_agent = LlmAgent(
    name="servicenow_agent",
    model="gemini-2.5-flash",
    output_schema=ServiceNowOutput,
    instruction=servicenow_agent_instruction,
    tools=[create_servicenow_incident_from_state],
    after_model_callback=after_model_callback_def,
)