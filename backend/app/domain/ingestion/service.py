from __future__ import annotations

import json
import re
from typing import Protocol

from app.ai.client import AIClient, CompletionInput
from app.ai.json_extract import extract_json_object
from app.core.runtime import Clock
from app.domain.ingestion.model import IngestInput, ParsedReceipt, Result
from app.domain.transactions.model import CreateInput, Transaction
from app.domain.transactions.service import TransactionService

AMOUNT_PATTERN = re.compile(r"(?i)(\d[\d\.,]*)(k)?")
TAG_PATTERN = re.compile(r"#([A-Za-z0-9_]+)")


class ReceiptRepository(Protocol):
    def save_parsed_receipt(self, receipt: ParsedReceipt) -> ParsedReceipt: ...


class IngestionService:
    def __init__(self, transactions: TransactionService, receipts: ReceiptRepository, ai_client: AIClient, clock: Clock, model: str, prompt: str, prompt_source: str) -> None:
        self._transactions = transactions
        self._receipts = receipts
        self._ai_client = ai_client
        self._clock = clock
        self._model = model
        self._prompt = prompt
        self._prompt_source = prompt_source

    def ingest_chat(self, input_data: IngestInput) -> Result:
        raw = input_data.raw_input.strip()
        if not raw:
            raise ValueError("rawInput is required")
        regex_amount = extract_amount(raw)
        regex_tags = extract_tags(raw)
        suggestion, llm_payload = self._build_suggestion(raw, regex_amount, regex_tags)
        final_amount = max(1, regex_amount or suggestion["amount"])
        tx = self._transactions.create(
            CreateInput(
                occurredAt=self._clock.now(),
                type=coalesce_type(suggestion["action"], fallback_type(raw)),
                amount=final_amount,
                currency=suggestion["currency"] or "VND",
                jarCode=suggestion["jar_category"] or guess_jar(raw),
                goalName=suggestion["goal_name"],
                accountName=suggestion["account_name"],
                isFixed=suggestion["is_fixed"] or looks_fixed(raw),
                note=build_clean_note(raw, regex_tags, suggestion["clean_note"]),
                source=input_data.source or "chat",
                status="draft",
            )
        )
        receipt = self._receipts.save_parsed_receipt(
            ParsedReceipt(
                id=f"RCPT-{int(self._clock.now().timestamp() * 1_000_000_000)}",
                transactionId=tx.id,
                rawInput=raw,
                regexAmount=regex_amount,
                regexTags=regex_tags,
                llmModel=self._model or "configurable-parser",
                llmOutputJson=json.dumps(llm_payload),
                validationNote=validation_note(regex_amount, suggestion["amount"]),
                confidence=confidence_label(regex_amount, suggestion["jar_category"]),
                promptSource=self._prompt_source or "none",
                createdAt=self._clock.now(),
            )
        )
        return Result(transactionId=tx.id, receipt=receipt)

    def _build_suggestion(self, raw: str, regex_amount: int, regex_tags: list[str]) -> tuple[dict[str, object], dict[str, object]]:
        fallback = {
            "action": fallback_type(raw),
            "amount": regex_amount,
            "jar_category": guess_jar(raw),
            "is_fixed": looks_fixed(raw),
            "clean_note": build_clean_note(raw, regex_tags, raw),
            "tags": regex_tags,
            "currency": "VND",
            "goal_name": "",
            "account_name": "",
        }
        prompt = render_prompt(self._prompt, raw, regex_amount, regex_tags)
        try:
            output = self._ai_client.complete(CompletionInput(model=self._model, prompt=prompt))
            parsed = parse_suggestion(output.text)
            merged = {**fallback, **{k: v for k, v in parsed.items() if v not in ("", None, [], 0, False)}}
            return merged, {"provider_used": True, "model": output.model or self._model, "suggestion": merged}
        except Exception:
            return fallback, {"provider_used": False, "model": self._model or "configurable-parser", "suggestion": fallback}


def extract_amount(raw: str) -> int:
    match = AMOUNT_PATTERN.search(raw.replace(" ", ""))
    if not match:
        return 0
    cleaned = match.group(1).replace(".", "").replace(",", "")
    try:
        value = int(cleaned)
    except ValueError:
        return 0
    if match.group(2) and match.group(2).lower() == "k":
        value *= 1000
    return value


def extract_tags(raw: str) -> list[str]:
    return [match.group(1) for match in TAG_PATTERN.finditer(raw)]


def fallback_type(raw: str) -> str:
    return "IN" if "thu" in raw.lower() else "OUT"


def guess_jar(raw: str) -> str:
    lowered = raw.lower()
    if "qua" in lowered or "dam cuoi" in lowered:
        return "ChoDi"
    if "khoa hoc" in lowered or "sach" in lowered:
        return "GiaoDuc"
    if "vang" in lowered or "co phieu" in lowered:
        return "TuDoTaiChinh"
    if "xe" in lowered or "tiet kiem" in lowered:
        return "TietKiem"
    if any(token in lowered for token in ["an", "uong", "nha hang", "nhau"]):
        return "HuongThu"
    return "ThietYeu"


def looks_fixed(raw: str) -> bool:
    lowered = raw.lower()
    return any(token in lowered for token in ["tien nha", "rent", "spotify", "netflix"])


def build_clean_note(raw: str, regex_tags: list[str], suggested: str) -> str:
    clean = suggested.strip() or raw.strip()
    if regex_tags and "#" not in clean:
        clean = f"{clean} {' '.join(f'#{tag}' for tag in regex_tags)}".strip()
    return clean


def render_prompt(template: str, raw: str, regex_amount: int, regex_tags: list[str]) -> str:
    if template.strip():
        return template.replace("{{raw_input}}", raw).replace("{{regex_amount}}", str(regex_amount)).replace("{{regex_tags_json}}", json.dumps(regex_tags))
    return (
        "You are a transaction parser.\nReturn strict JSON with keys:\n"
        "action, amount, jar_category, is_fixed, clean_note, tags, currency, goal_name, account_name.\n\n"
        f"Raw input: {raw}\nRegex amount: {regex_amount}\nRegex tags: {json.dumps(regex_tags)}"
    )


def parse_suggestion(raw: str) -> dict[str, object]:
    try:
        return json.loads(extract_json_object(raw))
    except json.JSONDecodeError as exc:
        raise ValueError("could not parse llm suggestion json") from exc


def validation_note(regex_amount: int, suggested_amount: object) -> str:
    if regex_amount > 0 and int(suggested_amount or 0) > 0 and int(suggested_amount or 0) != regex_amount:
        return "amount overridden by regex after llm mismatch"
    if regex_amount > 0:
        return "amount validated by regex"
    if int(suggested_amount or 0) > 0:
        return "amount supplied by llm fallback"
    return "amount missing, fallback minimum applied"


def confidence_label(regex_amount: int, jar_category: object) -> str:
    if regex_amount > 0 and str(jar_category or "").strip():
        return "high"
    if regex_amount > 0:
        return "medium"
    return "low"


def coalesce_type(raw: object, fallback: str) -> str:
    value = str(raw).strip().upper()
    return value if value in {"IN", "OUT", "TRANSFER"} else fallback
