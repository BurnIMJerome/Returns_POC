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
from .instruction import validation_agent_instruction
from google.adk.tools.tool_context   import ToolContext 
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse
import json


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

def after_model_callback_def(
    callback_context: CallbackContext,
    llm_response: LlmResponse
) -> Optional[LlmResponse]:


    # --- Robust debug logging and safer extraction ---
    def get_llm_text(llm_response):
        try:
            print("[DEBUG] Raw LLM response object:", repr(llm_response))
            if not llm_response or not hasattr(llm_response, "content"):
                print("[DEBUG] llm_response missing content attribute.")
                return None
            content = llm_response.content
            print("[DEBUG] LLM response content:", repr(content))
            if not hasattr(content, "parts") or not content.parts or len(content.parts) == 0:
                print("[DEBUG] content missing parts or parts is empty.")
                return None
            print("[DEBUG] LLM response content parts:", repr(content.parts))
            part = content.parts[0]
            if hasattr(part, "text") and part.text and part.text.strip():
                return part.text.strip()
            print("[DEBUG] part missing text or text is empty.")
            return None
        except Exception as e:
            print(f"[ERROR] Exception extracting LLM text: {e}")
            return None

    original_text = get_llm_text(llm_response)
    if not original_text:
        print("\n[AFTER MODEL] LLM response is empty or malformed.")
        print("[DEBUG] Full LLM response for diagnosis:", repr(llm_response))
        return llm_response

    modified_llm_response = copy.deepcopy(llm_response)
    print(f"\n[AFTER MODEL] Original LLM response: {original_text}")

    # Save raw validation result
    callback_context.state["validation_result"] = original_text

    # Try to parse the model output as JSON and, if validation passed, create a ServiceNow
    # incident programmatically (so the agent doesn't rely solely on the LLM to call the tool).
    def try_force_json(text):
        import re
        # Try to extract the first {...} JSON object from the text
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception as e:
                print(f"[AFTER_MODEL] force_json extraction failed: {e}")
        return None

    try:
        parsed = json.loads(original_text)
    except Exception as e1:
        print(f"[AFTER_MODEL] JSON parse failed: {e1}")
        # Try to force extract a JSON object from the text
        parsed = try_force_json(original_text)
        if parsed is not None:
            print("[AFTER_MODEL] Successfully extracted JSON substring from malformed output.")
        else:
            print("[AFTER_MODEL] Could not extract JSON from LLM output. Returning error.")
        # Not JSON — return a structured ValidationErrorOutput so downstream code
        # receives a clear, machine-readable error instead of ambiguous text.
        error_obj = {
            "result": {
                "status": "error",
                "error_type": "validation_error",
                "message": "The validation process did not return a clear outcome. Raw LLM output: " + original_text[:500],
                "missing_fields": [],
                "next_step": "Ensure the model returns the OutputSchema JSON exactly as specified and re-run."
            }
        }
        try:
            modified_llm_response.content.parts[0].text = json.dumps(error_obj)
            callback_context.state["validation_result_enriched"] = error_obj
        except Exception:
            pass
        return modified_llm_response

    # Expecting structure: {"result": {...}} where result contains validation metadata
    result_obj = parsed.get("result") if isinstance(parsed, dict) else None
    # Debug dump: print the parsed JSON (safe fallback to str if not serializable)
    try:
        pretty = json.dumps(parsed, indent=2)
    except Exception:
        pretty = str(parsed)
    print(f"[AFTER_MODEL] Parsed LLM JSON:\n{pretty}")
    # Also print the extracted result object for quick visibility
    try:
        pretty_result = json.dumps(result_obj, indent=2) if isinstance(result_obj, dict) else str(result_obj)
    except Exception:
        pretty_result = str(result_obj)
    print(f"[AFTER_MODEL] Extracted result object:\n{pretty_result}")
    # Ensure Created_Date is present; if not, set to today
    if isinstance(result_obj, dict):
        created_date = result_obj.get("Created_Date")
        if not created_date:
            # Set to today in ISO format
            today = datetime.now().isoformat()
            result_obj["Created_Date"] = today
            print(f"[AFTER_MODEL] Created_Date missing, set to today: {today}")
    if not isinstance(result_obj, dict):
        # Malformed result — return structured ValidationErrorOutput
        error_obj = {
            "result": {
                "status": "error",
                "error_type": "validation_error",
                "message": "The validation output did not contain the expected 'result' object.",
                "missing_fields": [],
                "next_step": "Ensure the model returns a top-level 'result' object matching OutputSchema."
            }
        }
        try:
            modified_llm_response.content.parts[0].text = json.dumps(error_obj)
            callback_context.state["validation_result_enriched"] = error_obj
        except Exception:
            pass
        return modified_llm_response


    # --- Ensure actual BigQuery insert is performed and log the result ---
    validation_status = result_obj.get("validation_status")
    if (
        validation_status == "passed"
        and result_obj.get("status", "").lower() == "not_rma"
    ):
        print("[DEBUG] Fixing status from 'not_rma' to 'Pending' for valid RMA.")
        result_obj["status"] = "Pending"

    # Only attempt insert if this is an RMA (not not_rma or error)

    if result_obj.get("status") not in ("not_rma", "error"):
        # Remove insert_metadata if present (will be set by actual insert)
        result_obj.pop("insert_metadata", None)
        # Prepare row for insert (filter only BigQuery columns)
        bq_row = {k: v for k, v in result_obj.items() if k in [
            "Customer_ID", "Order_Number", "Invoice_Number", "RMA_Type", "Reason_Code", "Status", "Priority", "Created_Date", "Approved_Date", "Closed_Date", "Created_By", "Source_Channel"
        ]}
        print("[DEBUG] Actual BigQuery insert row:", json.dumps(bq_row, indent=2))
        try:
            from google.cloud import bigquery
            client = bigquery.Client(project=settings.BIGQUERY_PROJECT)
            table_ref = f"{settings.BIGQUERY_PROJECT}.{settings.BIGQUERY_DATASET}.{settings.BIGQUERY_TABLE}"
            errors = client.insert_rows_json(table_ref, [bq_row])
            if errors:
                print("[ERROR] BigQuery insert errors:", errors)
                result_obj["insert_metadata"] = {
                    "insert_status": "failed",
                    "inserted_row_id": None,
                    "insert_error": str(errors)
                }
            else:
                print("[DEBUG] BigQuery insert successful")
                result_obj["insert_metadata"] = {
                    "insert_status": "inserted",
                    "inserted_row_id": None,
                    "insert_error": None
                }
        except Exception as e:
            print("[ERROR] Exception during BigQuery insert:", str(e))
            result_obj["insert_metadata"] = {
                "insert_status": "failed",
                "inserted_row_id": None,
                "insert_error": str(e)
            }

    # Debug print: show payload to bigquery_insert_agent (now actual insert)
    print("[DEBUG] Payload to bigquery_insert_agent:", json.dumps(result_obj, indent=2))

    if validation_status not in ("passed", "failed", "skipped"):
        error_obj = {
            "result": {
                "status": "error",
                "error_type": "validation_error",
                "message": "The validation process did not return a clear outcome.",
                "missing_fields": [],
                "next_step": "Ensure the model populates 'validation_status' with 'passed' or 'failed'."
            }
        }
        try:
            modified_llm_response.content.parts[0].text = json.dumps(error_obj)
            callback_context.state["validation_result_enriched"] = error_obj
        except Exception:
            pass
        return modified_llm_response
    case_status = result_obj.get("case_status")

    # If validation passed, ensure a real ServiceNow incident exists.
    # The model may fabricate a `case_status`/`case_number` without actually calling the tool.
    if validation_status == "passed":
        # helper to check whether an existing case (by sys_id or number) is present in SNOW
        def verify_case_exists(sys_id: Optional[str], number: Optional[str]) -> bool:
            try:
                if sys_id:
                    # try get by sys_id
                    resp = snow_get_record(sys_id=sys_id, table="incident")
                    # snow_get_record returns parsed JSON with 'result' or the record directly
                    if isinstance(resp, dict) and (resp.get("result") or resp.get("sys_id") or resp.get("number")):
                        return True
                if number:
                    # query by number
                    q = f"number={number}"
                    resp = snow_query_records(table="incident", query=q, limit=1)
                    results = None
                    if isinstance(resp, dict):
                        results = resp.get("result") or resp.get("records") or resp.get("items")
                    if isinstance(results, list) and len(results) > 0:
                        return True
            except Exception as e:
                print(f"[AFTER_MODEL] verify_case_exists check raised: {e}")
            return False

        # If LLM claims case already created, verify it; if verification fails, we'll create it.
        claimed_sys_id = result_obj.get("case_sys_id")
        claimed_number = result_obj.get("case_number")
        already_created_claim = case_status == "created"

        need_create = True
        if already_created_claim:
            try:
                exists = verify_case_exists(claimed_sys_id, claimed_number)
                if exists:
                    # Verified: nothing to do
                    need_create = False
                    print(f"[AFTER_MODEL] LLM claimed case created and verification succeeded: sys_id={claimed_sys_id} number={claimed_number}")
                else:
                    print(f"[AFTER_MODEL] LLM claimed case created but verification failed; will create a real incident. claimed_sys_id={claimed_sys_id} claimed_number={claimed_number}")
            except Exception as e:
                print(f"[AFTER_MODEL] Error verifying claimed case: {e}; will attempt to create case.")
                need_create = True

        if need_create:
            # build ServiceNow fields safely
            try:
                # helper: recursively search parsed JSON for a key (case-insensitive)
                def find_key(obj, target_key_lower):
                    if obj is None:
                        return None
                    if isinstance(obj, dict):
                        for k, v in obj.items():
                            if k.lower() == target_key_lower:
                                return v
                            res = find_key(v, target_key_lower)
                            if res is not None:
                                return res
                    elif isinstance(obj, list):
                        for item in obj:
                            res = find_key(item, target_key_lower)
                            if res is not None:
                                return res
                    return None

                # try multiple places: result_obj, full parsed JSON
                def extract_field(name):
                    key = name.lower()
                    val = None
                    # 1) check result_obj directly
                    if isinstance(result_obj, dict):
                        val = find_key(result_obj, key)
                    # 2) check whole parsed document
                    if val is None:
                        val = find_key(parsed, key)
                    # 3) fallback to callback state (e.g., full_message metadata)
                    if val is None:
                        fm = callback_context.state.get("full_message")
                        val = find_key(fm, key) if fm else None
                    return val

                customer_id = extract_field("Customer_ID") or ""
                rma_type = extract_field("RMA_Type") or "N/A"
                reason_code = extract_field("Reason_Code") or "N/A"
                order_number = extract_field("Order_Number") or "N/A"
                invoice_number = extract_field("Invoice_Number") or "N/A"
                priority = extract_field("Priority") or "N/A"


                # Fallback for short_description: use placeholder if Customer_ID is missing or blank
                short_desc_customer = customer_id.strip() if customer_id and customer_id.strip() else ""
                short_description = f"RMA Request from Email - Customer {short_desc_customer}".strip()
                if not short_desc_customer:
                    short_description = "RMA Request from Email - Customer (No ID Provided)"

                table = "incident"
                fields = {
                    "short_description": short_description,
                    "description": (
                        f"RMA Type: {rma_type}\nReason Code: {reason_code}\nOrder Number: {order_number}\nInvoice Number: {invoice_number}\nPriority: {priority}"
                    ),
                }

                # Log fields being sent for debugging
                print(f"[AFTER_MODEL] Creating ServiceNow incident with fields: {fields}")

                # Call the tool directly. It will raise if credentials are missing; capture errors.
                sn_response = snow_create_record(table=table, fields=fields)

                # Normalize response and update parsed result
                resp_result = sn_response.get("result") if isinstance(sn_response, dict) and "result" in sn_response else sn_response

                result_obj["case_status"] = "created"
                # try to extract common fields
                result_obj["case_sys_id"] = None
                result_obj["case_number"] = None
                if isinstance(resp_result, dict):
                    result_obj["case_sys_id"] = resp_result.get("sys_id") or resp_result.get("result", {}).get("sys_id")
                    result_obj["case_number"] = resp_result.get("number") or resp_result.get("result", {}).get("number")
            except Exception as e:
                # ServiceNow creation failed — record error so the caller can report it
                result_obj["case_status"] = "failed"
                result_obj["case_sys_id"] = None
                result_obj["case_number"] = None
                result_obj["case_error"] = str(e)

    # write back the modified JSON into the response so downstream code sees it
        try:
            modified_text = json.dumps(parsed)
            modified_llm_response = json.dumps(parsed)
            # Replace the LLM response text with the enriched JSON
            llm_response.content.parts[0].text = modified_text
            # Save the enriched response in state too
            callback_context.state["validation_result_enriched"] = parsed
        except Exception:
            pass

    case_id = callback_context.state.get("CaseID")

    # 🔹 SIMPLE STRING CHECK
    # if case_id and '"insert_status": "inserted"' in original_text:
    #     success_message = f"Successfully created case. Your Case ID: {case_id}"
    #     modified_llm_response.content.parts[0].text = success_message

    #     print("[AFTER MODEL] Overriding response with success message.")
    #     return modified_llm_response

    # Always return the (possibly modified) llm_response
    # Add a user_message field to the JSON if case was created and BigQuery insert succeeded
    try:
        parsed_final = json.loads(llm_response.content.parts[0].text)
        result = parsed_final.get("result", {}) if isinstance(parsed_final, dict) else {}
        case_number = result.get("case_number")
        validation_status = result.get("validation_status")
        case_status = result.get("case_status")
        insert_metadata = result.get("insert_metadata", {})
        insert_status = insert_metadata.get("insert_status")
        if (
            validation_status == "passed"
            and case_status == "created"
            and case_number
            and insert_status == "inserted"
        ):
            user_message = (
                "Validation of the email content has passed, and the RMA details have been successfully extracted. "
                "The RMA record has been inserted into BigQuery. "
                f"An RMA case has been created with Case ID: {case_number}.\n\n"
                "Do you want to open another email, view unread emails, or view latest emails?"
            )
            # Attach user_message to the result
            parsed_final["user_message"] = user_message
            llm_response.content.parts[0].text = json.dumps(parsed_final)
    except Exception:
        pass
    return llm_response






# --- BigQueryToolset setup for direct use ---
application_default_credentials, _ = google.auth.default()
credentials_config = BigQueryCredentialsConfig(credentials=application_default_credentials)
tool_config = BigQueryToolConfig(
    write_mode=WriteMode.ALLOWED,
    location=getattr(settings, "GOOGLE_CLOUD_LOCATION", "asia-southeast1")
)
bigquery_toolset = BigQueryToolset(credentials_config=credentials_config, bigquery_tool_config=tool_config)

validation_agent = LlmAgent(
    name="validation_agent",
    model="gemini-2.5-flash",
    output_schema=OutputSchema,
    instruction=validation_agent_instruction,
    tools=[
        validateEmailIfRMA,
        bigquery_toolset,
        snow_create_record,
        snow_get_record,
        snow_query_records
    ],
    after_model_callback=after_model_callback_def,
)
