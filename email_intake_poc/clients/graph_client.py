from __future__ import annotations
from typing import Any, Dict, List, Optional
from google.adk.tools.tool_context import ToolContext 
import requests
import msal

from ..config import settings
from urllib.parse import quote

GRAPH_BASE = "https://graph.microsoft.com/v1.0"


class GraphMailClient:
    """Microsoft Graph REST client using App-only auth (client credentials)."""

    def __init__(self):
        # Do not raise during import — defer validation until the client is actually used.
        self.tenant_id = settings.AZURE_TENANT_ID
        self.client_id = settings.AZURE_CLIENT_ID
        self.client_secret = settings.AZURE_CLIENT_SECRET

        self.authority = (
            f"https://login.microsoftonline.com/{self.tenant_id}"
            if self.tenant_id
            else None
        )
        self._token: Optional[str] = None
        # track whether configuration is complete
        self._configured = bool(
            self.tenant_id and self.client_id and self.client_secret and settings.MAILBOX_UPN
        )

    def _get_token(self) -> str:
        # simple in-memory token cache
        if self._token:
            return self._token

        if not self._configured:
            missing = []
            if not self.tenant_id:
                missing.append("AZURE_TENANT_ID")
            if not self.client_id:
                missing.append("AZURE_CLIENT_ID")
            if not self.client_secret:
                missing.append("AZURE_CLIENT_SECRET")
            if not settings.MAILBOX_UPN:
                missing.append("MAILBOX_UPN")
            raise ValueError(f"Missing env vars: {', '.join(missing)}")

        app = msal.ConfidentialClientApplication(
            self.client_id,
            authority=self.authority,
            client_credential=self.client_secret,
        )
        result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
        if "access_token" not in result:
            raise RuntimeError(result.get("error_description") or str(result))

        self._token = result["access_token"]
        return self._token

    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self._get_token()}"}

    def list_inbox_messages(self, top: int = 10, unread_only: bool = True) -> List[Dict[str, Any]]:
        user_upn = settings.MAILBOX_UPN
        url = f"{GRAPH_BASE}/users/{user_upn}/mailFolders/Inbox/messages"

        params: Dict[str, str] = {
            "$top": str(top),
            "$select": "id,subject,from,receivedDateTime,bodyPreview,isRead",
            "$orderby": "receivedDateTime desc",
        }
        if unread_only:
            params["$filter"] = "isRead eq false"

        r = requests.get(url, headers=self._headers(), params=params, timeout=30)
        r.raise_for_status()
        return r.json().get("value", [])

    def get_message(self, message_id: str, prefer_text: bool = True) -> Dict[str, Any]:
        user_upn = settings.MAILBOX_UPN
        # message IDs can contain characters that need quoting when used in a path segment
        quoted_id = quote(message_id, safe="")
        url = f"{GRAPH_BASE}/users/{user_upn}/messages/{quoted_id}"

        headers = self._headers()
        if prefer_text:
            headers["Prefer"] = 'outlook.body-content-type="text"'

        params = {"$select": "id,subject,from,receivedDateTime,body,isRead"}
        r = requests.get(url, headers=headers, params=params, timeout=30)
        try:
            r.raise_for_status()
        except requests.HTTPError:
            # capture helpful debug info for diagnosing 404s (message id, URL, status, body)
            try:
                req_url = r.request.url
            except Exception:
                req_url = url
            # include the quoted id so it's easy to correlate with the raw id returned earlier
            print(
                "GraphMailClient.get_message: HTTP error when fetching message",
                {
                    "message_id": message_id,
                    "quoted_id": quoted_id,
                    "request_url": req_url,
                    "status_code": r.status_code,
                    "response_text_snippet": (r.text or "")[:1000],
                },
            )
            # re-raise so callers see the original HTTPError
            raise
        return r.json()

    def mark_as_read(self, message_id: str) -> None:
        user_upn = settings.MAILBOX_UPN
        quoted_id = quote(message_id, safe="")
        url = f"{GRAPH_BASE}/users/{user_upn}/messages/{quoted_id}"

        r = requests.patch(
            url,
            headers={**self._headers(), "Content-Type": "application/json"},
            json={"isRead": True},
            timeout=30,
        )
        r.raise_for_status()
