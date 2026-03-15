import httpx

from app.ai.client import (
    AIClientError,
    CompletionInput,
    GeminiClient,
    NoopClient,
    OllamaClient,
    OpenAIClient,
    build_ai_client,
)
from app.core.config import Settings


def test_build_ai_client_returns_noop_when_unconfigured() -> None:
    client = build_ai_client(Settings())

    assert isinstance(client, NoopClient)


def test_openai_client_complete() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/responses"
        assert request.headers["Authorization"] == "Bearer test-key"
        return httpx.Response(
            200,
            json={
                "model": "gpt-5-mini",
                "output_text": '{"action":"OUT","amount":500000}',
            },
        )

    transport = httpx.MockTransport(handler)
    client = OpenAIClient(
        api_key="test-key",
        base_url="https://example.test",
        http_client=httpx.Client(transport=transport),
    )

    result = client.complete(CompletionInput(model="gpt-5-mini", prompt="prompt"))

    assert '"amount":500000' in result.text
    assert result.model == "gpt-5-mini"


def test_gemini_client_complete() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1beta/models/gemini-2.5-flash:generateContent"
        assert request.url.params["key"] == "test-key"
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {
                                    "text": '{"action":"IN","amount":1000000}',
                                }
                            ]
                        }
                    }
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    client = GeminiClient(
        api_key="test-key",
        base_url="https://example.test",
        http_client=httpx.Client(transport=transport),
    )

    result = client.complete(CompletionInput(model="gemini-2.5-flash", prompt="prompt"))

    assert '"amount":1000000' in result.text
    assert result.model == "gemini-2.5-flash"


def test_openai_client_raises_on_empty_output() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"model": "gpt-5-mini", "output_text": ""})

    transport = httpx.MockTransport(handler)
    client = OpenAIClient(
        api_key="test-key",
        base_url="https://example.test",
        http_client=httpx.Client(transport=transport),
    )

    try:
        client.complete(CompletionInput(model="gpt-5-mini", prompt="prompt"))
    except AIClientError as exc:
        assert "no text output" in str(exc)
    else:
        raise AssertionError("expected AIClientError")


def test_ollama_client_complete() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/generate"
        payload = request.read().decode()
        assert "gemma3:27b" in payload
        return httpx.Response(
            200,
            json={
                "model": "gemma3:27b",
                "response": '{"action":"OUT","amount":250000}',
            },
        )

    transport = httpx.MockTransport(handler)
    client = OllamaClient(
        base_url="http://localhost:11434",
        http_client=httpx.Client(transport=transport),
    )

    result = client.complete(CompletionInput(model="gemma3:27b", prompt="prompt"))

    assert '"amount":250000' in result.text
    assert result.model == "gemma3:27b"


def test_build_ai_client_supports_ollama_without_api_key() -> None:
    settings = Settings.model_validate(
        {
            "ai": {
                "provider": "ollama",
                "base_url": "http://localhost:11434",
                "model": "gemma3:27b",
            }
        }
    )

    client = build_ai_client(settings)

    assert isinstance(client, OllamaClient)
