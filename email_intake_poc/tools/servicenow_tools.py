from __future__ import annotations

import os
from typing import Any, Dict, Optional

import requests

SNOW_INSTANCE_NAME = os.getenv("SNOW_INSTANCE_NAME", "").strip()
SNOW_USERNAME = os.getenv("SNOW_USERNAME", "").strip()
SNOW_PASSWORD = os.getenv("SNOW_PASSWORD", "").strip()
SNOW_DEFAULT_TABLE = os.getenv("SNOW_DEFAULT_TABLE", "incident").strip()
SNOW_VERIFY_TLS = os.getenv("SNOW_VERIFY_TLS", "true").lower() == "true"
SNOW_TIMEOUT_SECONDS = int(os.getenv("SNOW_TIMEOUT_SECONDS", "30"))

BASE_URL = f"https://{SNOW_INSTANCE_NAME}.service-now.com".rstrip("/")


def _auth() -> tuple[str, str]:
    if not SNOW_INSTANCE_NAME:
        raise ValueError("Missing SNOW_INSTANCE_NAME (e.g., dev12345)")
    if not SNOW_USERNAME or not SNOW_PASSWORD:
        raise ValueError("Missing SNOW_USERNAME / SNOW_PASSWORD in environment variables")
    return (SNOW_USERNAME, SNOW_PASSWORD)


def _headers() -> Dict[str, str]:
    return {"Accept": "application/json", "Content-Type": "application/json"}


def _raise_for_status_with_body(resp: requests.Response) -> None:
    """ServiceNow often returns useful JSON errors; surface them."""
    try:
        resp.raise_for_status()
    except requests.HTTPError as e:
        body = ""
        try:
            body = resp.text
        except Exception:
            body = "<unable to read response body>"
        raise requests.HTTPError(f"{e} | Response body: {body}") from None


def snow_create_record(
    table: str = SNOW_DEFAULT_TABLE,
    fields: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    fields = fields or {}
    url = f"{BASE_URL}/api/now/table/{table}"

    # Block empty or missing short_description (likely LLM direct call)
    if not fields or not fields.get("short_description"):
        print("[ERROR] Attempted ServiceNow incident creation with empty or missing short_description. This call is blocked to prevent blank tickets. Only call this tool from Python logic with a valid short_description.")
        raise ValueError("Blocked: ServiceNow incident creation attempted with empty or missing short_description.")

    # Debug: print outgoing payload
    print(f"[DEBUG] ServiceNow create_record payload: {fields}")

    resp = requests.post(
        url,
        json=fields,
        headers=_headers(),
        auth=_auth(),
        timeout=SNOW_TIMEOUT_SECONDS,
        verify=SNOW_VERIFY_TLS,
    )
    # Debug: print response from ServiceNow
    print(f"[DEBUG] ServiceNow create_record response: {resp.status_code} {resp.text}")

    _raise_for_status_with_body(resp)
    return resp.json()


def snow_get_record(
    sys_id: str,
    table: str = SNOW_DEFAULT_TABLE,
    fields: Optional[str] = None,
) -> Dict[str, Any]:
    url = f"{BASE_URL}/api/now/table/{table}/{sys_id}"
    params: Dict[str, str] = {}
    if fields:
        params["sysparm_fields"] = fields

    resp = requests.get(
        url,
        params=params,
        headers=_headers(),
        auth=_auth(),
        timeout=SNOW_TIMEOUT_SECONDS,
        verify=SNOW_VERIFY_TLS,
    )
    _raise_for_status_with_body(resp)
    return resp.json()


def snow_query_records(
    table: str = SNOW_DEFAULT_TABLE,
    query: str = "",
    limit: int = 10,
    fields: Optional[str] = None,
) -> Dict[str, Any]:
    url = f"{BASE_URL}/api/now/table/{table}"
    params: Dict[str, str] = {"sysparm_limit": str(limit)}
    if query:
        params["sysparm_query"] = query
    if fields:
        params["sysparm_fields"] = fields

    resp = requests.get(
        url,
        params=params,
        headers=_headers(),
        auth=_auth(),
        timeout=SNOW_TIMEOUT_SECONDS,
        verify=SNOW_VERIFY_TLS,
    )
    _raise_for_status_with_body(resp)
    return resp.json()


def snow_update_record(
    sys_id: str,
    fields: Dict[str, Any],
    table: str = SNOW_DEFAULT_TABLE,
) -> Dict[str, Any]:
    url = f"{BASE_URL}/api/now/table/{table}/{sys_id}"

    resp = requests.patch(
        url,
        json=fields,
        headers=_headers(),
        auth=_auth(),
        timeout=SNOW_TIMEOUT_SECONDS,
        verify=SNOW_VERIFY_TLS,
    )
    _raise_for_status_with_body(resp)
    return resp.json()


def snow_delete_record(
    sys_id: str,
    table: str = SNOW_DEFAULT_TABLE,
) -> Dict[str, Any]:
    url = f"{BASE_URL}/api/now/table/{table}/{sys_id}"

    resp = requests.delete(
        url,
        headers=_headers(),
        auth=_auth(),
        timeout=SNOW_TIMEOUT_SECONDS,
        verify=SNOW_VERIFY_TLS,
    )
    _raise_for_status_with_body(resp)
    return {"status": "deleted", "table": table, "sys_id": sys_id}