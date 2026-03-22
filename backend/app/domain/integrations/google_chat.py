from __future__ import annotations

from typing import Any, Protocol

from app.domain.ingestion.model import IngestInput, Result


class IngestionUseCase(Protocol):
    def ingest_chat(self, input_data: IngestInput) -> Result: ...


class GoogleChatService:
    def __init__(self, ingestion: IngestionUseCase) -> None:
        self._ingestion = ingestion

    def handle_event(self, payload: dict[str, Any]) -> dict[str, str]:
        event_type = str(payload.get("type") or payload.get("eventType") or "").upper()

        if event_type == "ADDED_TO_SPACE":
            return {
                "text": (
                    "Chao ban, toi la Turbo Potato. "
                    "Hay nhan tin cho toi theo kieu Google Chat nhu "
                    "`an trua 150k #food` hoac `/log an trua 150k #food` de tao draft giao dich."
                )
            }

        if event_type == "REMOVED_FROM_SPACE":
            return {}

        if event_type != "MESSAGE":
            return {"text": "Su kien nay chua duoc ho tro."}

        raw_input = extract_message_text(payload)
        if not raw_input:
            return {"text": "Khong tim thay noi dung giao dich. Hay gui mot tin nhan ngan gon ve thu, chi, hoac chuyen tien."}

        result = self._ingestion.ingest_chat(
            IngestInput(
                rawInput=raw_input,
                source="google-chat",
                actor=extract_actor(payload),
            )
        )

        return {
            "text": (
                f"Da tao draft giao dich {result.transaction_id}. "
                "Mo trang Review de xac nhan hoac chinh sua truoc khi chot."
            )
        }


def extract_message_text(payload: dict[str, Any]) -> str:
    message = payload.get("message")
    if not isinstance(message, dict):
        return ""

    argument_text = str(message.get("argumentText") or "").strip()
    if argument_text:
        return argument_text

    slash_command = message.get("slashCommand")
    if isinstance(slash_command, dict):
        command_id = str(slash_command.get("commandId") or "").strip()
        if command_id:
            text = str(message.get("text") or "").strip()
            return normalize_message_text(text)

    text = str(message.get("text") or "").strip()
    if text:
        return normalize_message_text(text)

    annotations = message.get("annotations")
    if isinstance(annotations, list):
        parts: list[str] = []
        for item in annotations:
            if not isinstance(item, dict):
                continue
            slash_data = item.get("slashCommand")
            if isinstance(slash_data, dict):
                prompt = str(slash_data.get("commandName") or "").strip()
                if prompt:
                    parts.append(prompt)
        return " ".join(parts).strip()

    return ""


def normalize_message_text(text: str) -> str:
    normalized = text.replace("\u00a0", " ").strip()
    if normalized.startswith("/"):
        segments = normalized.split(maxsplit=1)
        if len(segments) == 2:
            return segments[1].strip()
    return normalized


def extract_actor(payload: dict[str, Any]) -> str:
    user = payload.get("user")
    if not isinstance(user, dict):
        return "google-chat"
    return str(user.get("displayName") or user.get("name") or "google-chat").strip()
