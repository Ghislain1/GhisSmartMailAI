from __future__ import annotations

from typing import Any

import httpx
import msal

from .config import Settings

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
SCOPES = ["https://graph.microsoft.com/.default"]


class GraphClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._app = msal.ConfidentialClientApplication(
            settings.azure_client_id,
            authority=f"https://login.microsoftonline.com/{settings.azure_tenant_id}",
            client_credential=settings.azure_client_secret,
        )

    def _token(self) -> str:
        result = self._app.acquire_token_silent(SCOPES, account=None)
        if not result:
            result = self._app.acquire_token_for_client(scopes=SCOPES)
        if "access_token" not in result:
            raise RuntimeError(f"Failed to acquire token: {result.get('error_description', result)}")
        return result["access_token"]

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._token()}", "Content-Type": "application/json"}

    @property
    def _user_path(self) -> str:
        uid = self.settings.outlook_user_id or "me"
        return "me" if uid == "me" else f"users/{uid}"

    def request(self, method: str, path: str, *, params: dict[str, Any] | None = None, json: Any = None) -> httpx.Response:
        url = f"{GRAPH_BASE}/{self._user_path}/{path.lstrip('/')}"
        with httpx.Client(timeout=30.0) as client:
            resp = client.request(method, url, headers=self._headers(), params=params, json=json)
        resp.raise_for_status()
        return resp

    def get(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        resp = self.request("GET", path, params=params)
        if resp.status_code == 204 or not resp.content:
            return {}
        return resp.json()

    def post(self, path: str, *, json: Any = None) -> Any:
        resp = self.request("POST", path, json=json)
        if resp.status_code == 204 or not resp.content:
            return {"status": "ok"}
        return resp.json()

    def patch(self, path: str, *, json: Any = None) -> Any:
        resp = self.request("PATCH", path, json=json)
        if resp.status_code == 204 or not resp.content:
            return {"status": "ok"}
        return resp.json()
