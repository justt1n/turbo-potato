from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

import httpx
import jwt

from app.core.config import Settings
from app.infrastructure.sheets.types import SpreadsheetAdminAPI, ValuesAPI

SPREADSHEETS_SCOPE = "https://www.googleapis.com/auth/spreadsheets"


class GoogleSheetsError(RuntimeError):
    """Raised when Google Sheets auth or API calls fail."""


@dataclass(slots=True)
class ServiceAccountCredentials:
    client_email: str
    private_key: str
    token_uri: str


class ServiceAccountAuthorizer:
    def __init__(
        self,
        credentials: ServiceAccountCredentials,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._credentials = credentials
        self._http_client = http_client or httpx.Client(timeout=15.0)
        self._access_token = ""
        self._expires_at = 0.0

    def token(self) -> str:
        if self._access_token and (self._expires_at - time.time()) > 60:
            return self._access_token

        now = int(time.time())
        assertion = jwt.encode(
            {
                "iss": self._credentials.client_email,
                "scope": SPREADSHEETS_SCOPE,
                "aud": self._credentials.token_uri,
                "iat": now,
                "exp": now + 3600,
            },
            self._credentials.private_key,
            algorithm="RS256",
            headers={"typ": "JWT"},
        )

        response = self._http_client.post(
            self._credentials.token_uri,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                "assertion": assertion,
            },
        )
        if response.status_code >= 300:
            raise GoogleSheetsError(
                f"request access token: {response.status_code}: {response.text.strip()}"
            )

        payload = response.json()
        access_token = str(payload.get("access_token") or "").strip()
        expires_in = int(payload.get("expires_in") or 0)
        if not access_token or expires_in <= 0:
            raise GoogleSheetsError("request access token: missing access_token or expires_in")

        self._access_token = access_token
        self._expires_at = time.time() + expires_in
        return self._access_token


class GoogleValuesClient(ValuesAPI, SpreadsheetAdminAPI):
    def __init__(
        self,
        credentials: ServiceAccountCredentials,
        http_client: httpx.Client | None = None,
        authorizer: ServiceAccountAuthorizer | None = None,
    ) -> None:
        self._http_client = http_client or httpx.Client(timeout=15.0)
        self._authorizer = authorizer or ServiceAccountAuthorizer(credentials, self._http_client)

    @classmethod
    def from_settings(
        cls,
        settings: Settings,
        http_client: httpx.Client | None = None,
    ) -> "GoogleValuesClient":
        if not settings.use_google_sheets():
            raise GoogleSheetsError("google sheets is not configured")

        try:
            raw = json.loads(settings.sheets.service_account_json)
        except json.JSONDecodeError as exc:
            raise GoogleSheetsError(f"parse service account json: {exc}") from exc

        credentials = ServiceAccountCredentials(
            client_email=str(raw.get("client_email") or "").strip(),
            private_key=str(raw.get("private_key") or "").strip(),
            token_uri=str(raw.get("token_uri") or "").strip(),
        )
        if not credentials.client_email or not credentials.private_key or not credentials.token_uri:
            raise GoogleSheetsError("service account json is missing required fields")

        return cls(credentials, http_client=http_client)

    def append(self, spreadsheet_id: str, read_range: str, values: list[list[object]]) -> None:
        self._request(
            "POST",
            f"https://sheets.googleapis.com/v4/spreadsheets/{quote(spreadsheet_id, safe='')}/values/{quote(read_range, safe='')}:append",
            params={"valueInputOption": "RAW"},
            json_body={"values": values},
            error_prefix="append values",
        )

    def get(self, spreadsheet_id: str, read_range: str) -> list[list[object]]:
        response = self._request(
            "GET",
            f"https://sheets.googleapis.com/v4/spreadsheets/{quote(spreadsheet_id, safe='')}/values/{quote(read_range, safe='')}",
            error_prefix="get values",
        )
        payload = response.json()
        values = payload.get("values", [])
        if isinstance(values, list):
            return values
        raise GoogleSheetsError("decode get values payload: values field is not a list")

    def update(self, spreadsheet_id: str, read_range: str, values: list[list[object]]) -> None:
        self._request(
            "PUT",
            f"https://sheets.googleapis.com/v4/spreadsheets/{quote(spreadsheet_id, safe='')}/values/{quote(read_range, safe='')}",
            params={"valueInputOption": "RAW"},
            json_body={"values": values},
            error_prefix="update values",
        )

    def get_sheet_titles(self, spreadsheet_id: str) -> list[str]:
        response = self._request(
            "GET",
            f"https://sheets.googleapis.com/v4/spreadsheets/{quote(spreadsheet_id, safe='')}",
            params={"fields": "sheets.properties.title"},
            error_prefix="get spreadsheet",
        )
        payload = response.json()
        titles: list[str] = []
        for sheet in payload.get("sheets", []):
            properties = sheet.get("properties", {})
            title = str(properties.get("title") or "").strip()
            if title:
                titles.append(title)
        return titles

    def add_sheets(self, spreadsheet_id: str, titles: list[str]) -> None:
        if not titles:
            return

        requests = [
            {
                "addSheet": {
                    "properties": {
                        "title": title,
                    }
                }
            }
            for title in titles
        ]
        self._request(
            "POST",
            f"https://sheets.googleapis.com/v4/spreadsheets/{quote(spreadsheet_id, safe='')}:batchUpdate",
            json_body={"requests": requests},
            error_prefix="add sheets",
        )

    def _request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, str] | None = None,
        json_body: dict[str, Any] | None = None,
        error_prefix: str,
    ) -> httpx.Response:
        token = self._authorizer.token()
        response = self._http_client.request(
            method,
            url,
            params=params,
            json=json_body,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
        )
        if response.status_code >= 300:
            raise GoogleSheetsError(f"{error_prefix}: google sheets returned {response.status_code}: {response.text.strip()}")
        return response
