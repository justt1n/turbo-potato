from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import httpx

from app.core.config import Settings


class AIClientError(RuntimeError):
    """Raised when an AI provider request fails or returns invalid output."""


@dataclass(slots=True)
class CompletionInput:
    model: str
    prompt: str


@dataclass(slots=True)
class CompletionOutput:
    text: str
    model: str


class AIClient(Protocol):
    def complete(self, input_data: CompletionInput) -> CompletionOutput: ...


class NoopClient:
    def complete(self, input_data: CompletionInput) -> CompletionOutput:
        raise AIClientError("ai client is not configured")


def build_ai_client(settings: Settings) -> AIClient:
    provider = settings.ai.provider.strip().lower()
    if provider in {"", "none"}:
        return NoopClient()

    if provider == "openai":
        if not settings.ai.api_key.strip():
            return NoopClient()
        return OpenAIClient(
            api_key=settings.ai.api_key,
            base_url=settings.ai.base_url or "https://api.openai.com",
        )

    if provider in {"gemini", "google"}:
        if not settings.ai.api_key.strip():
            return NoopClient()
        return GeminiClient(
            api_key=settings.ai.api_key,
            base_url=settings.ai.base_url or "https://generativelanguage.googleapis.com",
        )

    if provider == "ollama":
        return OllamaClient(
            base_url=settings.ai.base_url or "http://localhost:11434",
        )

    return NoopClient()


class OpenAIClient:
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com",
        http_client: httpx.Client | None = None,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._http_client = http_client or httpx.Client(timeout=30.0)

    def complete(self, input_data: CompletionInput) -> CompletionOutput:
        response = self._http_client.post(
            f"{self._base_url}/v1/responses",
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": input_data.model,
                "input": input_data.prompt,
            },
        )
        if response.status_code >= 300:
            raise AIClientError(f"openai returned {response.status_code}: {response.text.strip()}")

        payload = response.json()
        text = str(payload.get("output_text") or "").strip()
        if not text:
            parts: list[str] = []
            for item in payload.get("output", []):
                for content in item.get("content", []):
                    candidate = str(content.get("text") or "").strip()
                    if candidate:
                        parts.append(candidate)
            text = "\n".join(parts).strip()

        if not text:
            raise AIClientError("openai response contained no text output")

        return CompletionOutput(
            text=text,
            model=str(payload.get("model") or input_data.model),
        )


class GeminiClient:
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://generativelanguage.googleapis.com",
        http_client: httpx.Client | None = None,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._http_client = http_client or httpx.Client(timeout=30.0)

    def complete(self, input_data: CompletionInput) -> CompletionOutput:
        response = self._http_client.post(
            f"{self._base_url}/v1beta/models/{input_data.model}:generateContent",
            params={"key": self._api_key},
            headers={"Content-Type": "application/json"},
            json={
                "contents": [
                    {
                        "parts": [
                            {
                                "text": input_data.prompt,
                            }
                        ]
                    }
                ]
            },
        )
        if response.status_code >= 300:
            raise AIClientError(f"gemini returned {response.status_code}: {response.text.strip()}")

        payload = response.json()
        parts: list[str] = []
        for candidate in payload.get("candidates", []):
            content = candidate.get("content", {})
            for part in content.get("parts", []):
                text = str(part.get("text") or "").strip()
                if text:
                    parts.append(text)

        output_text = "\n".join(parts).strip()
        if not output_text:
            raise AIClientError("gemini response contained no text output")

        return CompletionOutput(
            text=output_text,
            model=input_data.model,
        )


class OllamaClient:
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        http_client: httpx.Client | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._http_client = http_client or httpx.Client(timeout=60.0)

    def complete(self, input_data: CompletionInput) -> CompletionOutput:
        response = self._http_client.post(
            f"{self._base_url}/api/generate",
            headers={"Content-Type": "application/json"},
            json={
                "model": input_data.model,
                "prompt": input_data.prompt,
                "stream": False,
            },
        )
        if response.status_code >= 300:
            raise AIClientError(f"ollama returned {response.status_code}: {response.text.strip()}")

        payload = response.json()
        output_text = str(payload.get("response") or "").strip()
        if not output_text:
            raise AIClientError("ollama response contained no text output")

        return CompletionOutput(
            text=output_text,
            model=str(payload.get("model") or input_data.model),
        )
