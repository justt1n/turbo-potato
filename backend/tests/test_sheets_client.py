from __future__ import annotations

import json
from urllib.parse import parse_qs, urlparse

import httpx
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from app.core.config import Settings
from app.infrastructure.sheets.client import GoogleSheetsError, GoogleValuesClient


def service_account_json(token_uri: str = "https://oauth.example.test/token") -> str:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")
    return json.dumps(
        {
            "client_email": "robot@example.test",
            "private_key": pem,
            "token_uri": token_uri,
        }
    )


def test_google_client_rejects_missing_credentials() -> None:
    settings = Settings.model_validate(
        {
            "sheets": {
                "spreadsheet_id": "sheet-id",
                "service_account_json": json.dumps({"client_email": "robot@example.test"}),
            }
        }
    )

    try:
        GoogleValuesClient.from_settings(settings)
    except GoogleSheetsError as exc:
        assert "missing required fields" in str(exc)
    else:
        raise AssertionError("expected GoogleSheetsError")


def test_google_client_reuses_token_for_multiple_requests() -> None:
    token_requests = 0
    sheets_requests = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal token_requests, sheets_requests
        if request.url.path == "/token":
            token_requests += 1
            return httpx.Response(200, json={"access_token": "access-1", "expires_in": 3600})
        sheets_requests += 1
        assert request.headers["Authorization"] == "Bearer access-1"
        return httpx.Response(200, json={"values": [["A"]]})

    transport = httpx.MockTransport(handler)
    client = GoogleValuesClient.from_settings(
        Settings.model_validate(
            {
                "sheets": {
                    "spreadsheet_id": "sheet-id",
                    "service_account_json": service_account_json("https://oauth.example.test/token"),
                }
            }
        ),
        http_client=httpx.Client(transport=transport),
    )

    first = client.get("sheet-id", "Transactions!A1")
    second = client.get("sheet-id", "Transactions!A1")

    assert first == [["A"]]
    assert second == [["A"]]
    assert token_requests == 1
    assert sheets_requests == 2


def test_append_sends_expected_request() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/token":
            return httpx.Response(200, json={"access_token": "token", "expires_in": 3600})
        captured["method"] = request.method
        captured["url"] = str(request.url)
        captured["query"] = parse_qs(urlparse(str(request.url)).query)
        captured["body"] = json.loads(request.content.decode("utf-8"))
        return httpx.Response(200, json={})

    transport = httpx.MockTransport(handler)
    client = GoogleValuesClient.from_settings(
        Settings.model_validate(
            {
                "sheets": {
                    "spreadsheet_id": "sheet-id",
                    "service_account_json": service_account_json("https://oauth.example.test/token"),
                }
            }
        ),
        http_client=httpx.Client(transport=transport),
    )

    client.append("sheet-id", "Transactions!A:N", [["TX-1"]])

    assert captured["method"] == "POST"
    assert captured["url"].startswith(
        "https://sheets.googleapis.com/v4/spreadsheets/sheet-id/values/Transactions%21A%3AN:append"
    )
    assert captured["query"] == {"valueInputOption": ["RAW"]}
    assert captured["body"] == {"values": [["TX-1"]]}


def test_get_returns_values() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/token":
            return httpx.Response(200, json={"access_token": "token", "expires_in": 3600})
        return httpx.Response(200, json={"values": [["A1", "B1"]]})

    transport = httpx.MockTransport(handler)
    client = GoogleValuesClient.from_settings(
        Settings.model_validate(
            {
                "sheets": {
                    "spreadsheet_id": "sheet-id",
                    "service_account_json": service_account_json("https://oauth.example.test/token"),
                }
            }
        ),
        http_client=httpx.Client(transport=transport),
    )

    assert client.get("sheet-id", "Goals!1:1") == [["A1", "B1"]]


def test_update_sends_expected_request() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/token":
            return httpx.Response(200, json={"access_token": "token", "expires_in": 3600})
        captured["method"] = request.method
        captured["url"] = str(request.url)
        captured["query"] = parse_qs(urlparse(str(request.url)).query)
        captured["body"] = json.loads(request.content.decode("utf-8"))
        return httpx.Response(200, json={})

    transport = httpx.MockTransport(handler)
    client = GoogleValuesClient.from_settings(
        Settings.model_validate(
            {
                "sheets": {
                    "spreadsheet_id": "sheet-id",
                    "service_account_json": service_account_json("https://oauth.example.test/token"),
                }
            }
        ),
        http_client=httpx.Client(transport=transport),
    )

    client.update("sheet-id", "Goals!A1", [["Goal_Name"]])

    assert captured["method"] == "PUT"
    assert captured["url"].startswith(
        "https://sheets.googleapis.com/v4/spreadsheets/sheet-id/values/Goals%21A1"
    )
    assert captured["query"] == {"valueInputOption": ["RAW"]}
    assert captured["body"] == {"values": [["Goal_Name"]]}


def test_get_sheet_titles_extracts_titles() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/token":
            return httpx.Response(200, json={"access_token": "token", "expires_in": 3600})
        return httpx.Response(
            200,
            json={
                "sheets": [
                    {"properties": {"title": "Transactions"}},
                    {"properties": {"title": "Goals"}},
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    client = GoogleValuesClient.from_settings(
        Settings.model_validate(
            {
                "sheets": {
                    "spreadsheet_id": "sheet-id",
                    "service_account_json": service_account_json("https://oauth.example.test/token"),
                }
            }
        ),
        http_client=httpx.Client(transport=transport),
    )

    assert client.get_sheet_titles("sheet-id") == ["Transactions", "Goals"]


def test_add_sheets_builds_batch_update_payload() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/token":
            return httpx.Response(200, json={"access_token": "token", "expires_in": 3600})
        captured["method"] = request.method
        captured["path"] = request.url.path
        captured["body"] = json.loads(request.content.decode("utf-8"))
        return httpx.Response(200, json={})

    transport = httpx.MockTransport(handler)
    client = GoogleValuesClient.from_settings(
        Settings.model_validate(
            {
                "sheets": {
                    "spreadsheet_id": "sheet-id",
                    "service_account_json": service_account_json("https://oauth.example.test/token"),
                }
            }
        ),
        http_client=httpx.Client(transport=transport),
    )

    client.add_sheets("sheet-id", ["Reports", "Settings"])

    assert captured["method"] == "POST"
    assert captured["path"] == "/v4/spreadsheets/sheet-id:batchUpdate"
    assert captured["body"] == {
        "requests": [
            {"addSheet": {"properties": {"title": "Reports"}}},
            {"addSheet": {"properties": {"title": "Settings"}}},
        ]
    }


def test_non_2xx_raises_clear_exception() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/token":
            return httpx.Response(200, json={"access_token": "token", "expires_in": 3600})
        return httpx.Response(403, text="forbidden")

    transport = httpx.MockTransport(handler)
    client = GoogleValuesClient.from_settings(
        Settings.model_validate(
            {
                "sheets": {
                    "spreadsheet_id": "sheet-id",
                    "service_account_json": service_account_json("https://oauth.example.test/token"),
                }
            }
        ),
        http_client=httpx.Client(transport=transport),
    )

    try:
        client.get("sheet-id", "Transactions!A1")
    except GoogleSheetsError as exc:
        assert "google sheets returned 403" in str(exc)
    else:
        raise AssertionError("expected GoogleSheetsError")
