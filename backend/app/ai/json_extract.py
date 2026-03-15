from __future__ import annotations

import re

JSON_FENCE_PATTERN = re.compile(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", re.IGNORECASE)
JSON_OBJECT_PATTERN = re.compile(r"(\{[\s\S]*\})")


def extract_json_object(raw: str) -> str:
    text = raw.strip()
    fenced_match = JSON_FENCE_PATTERN.search(text)
    if fenced_match:
        return fenced_match.group(1).strip()

    plain_match = JSON_OBJECT_PATTERN.search(text)
    if plain_match:
        return plain_match.group(1).strip()

    raise ValueError("could not extract json object from llm response")
