from __future__ import annotations

from typing import Protocol

from app.domain.sources.model import CreateInput, Source, UpdateInput


class SourceRepository(Protocol):
    def create_source(self, source: Source) -> Source: ...

    def update_source(self, current_code: str, source: Source) -> Source: ...

    def list_sources(self) -> list[Source]: ...


class SourceService:
    def __init__(self, repo: SourceRepository) -> None:
        self._repo = repo

    def create(self, input_data: CreateInput) -> Source:
        code = normalize_code(input_data.code)
        name = input_data.name.strip()
        kind = input_data.kind.strip() or "wallet"
        provider = input_data.provider.strip()
        linked_jar_code = input_data.linked_jar_code.strip()
        if not code:
            raise ValueError("code is required")
        if not name:
            raise ValueError("name is required")
        if input_data.opening_balance < 0:
            raise ValueError("openingBalance must be zero or greater")
        if input_data.gold_quantity_chi < 0:
            raise ValueError("goldQuantityChi must be zero or greater")
        if input_data.gold_price_per_chi < 0:
            raise ValueError("goldPricePerChi must be zero or greater")
        if any(existing.code == code for existing in self._repo.list_sources()):
            raise ValueError(f"source {code} already exists")

        actual_balance = resolve_actual_balance(
            kind,
            input_data.actual_balance if input_data.actual_balance is not None else input_data.opening_balance,
            input_data.gold_quantity_chi,
            input_data.gold_price_per_chi,
        )

        source = Source(
            code=code,
            name=name,
            kind=kind,
            provider=provider,
            linkedJarCode=linked_jar_code,
            openingBalance=input_data.opening_balance,
            actualBalance=actual_balance,
            goldQuantityChi=input_data.gold_quantity_chi,
            goldPricePerChi=input_data.gold_price_per_chi,
            isActive=input_data.is_active,
            note=input_data.note.strip(),
        )
        return self._repo.create_source(source)

    def update(self, current_code: str, input_data: UpdateInput) -> Source:
        code = normalize_code(current_code)
        name = input_data.name.strip()
        kind = input_data.kind.strip() or "wallet"
        provider = input_data.provider.strip()
        linked_jar_code = input_data.linked_jar_code.strip()
        if not code:
            raise ValueError("code is required")
        if not name:
            raise ValueError("name is required")
        if input_data.opening_balance < 0:
            raise ValueError("openingBalance must be zero or greater")
        if input_data.actual_balance < 0:
            raise ValueError("actualBalance must be zero or greater")
        if input_data.gold_quantity_chi < 0:
            raise ValueError("goldQuantityChi must be zero or greater")
        if input_data.gold_price_per_chi < 0:
            raise ValueError("goldPricePerChi must be zero or greater")

        actual_balance = resolve_actual_balance(
            kind,
            input_data.actual_balance,
            input_data.gold_quantity_chi,
            input_data.gold_price_per_chi,
        )

        source = Source(
            code=code,
            name=name,
            kind=kind,
            provider=provider,
            linkedJarCode=linked_jar_code,
            openingBalance=input_data.opening_balance,
            actualBalance=actual_balance,
            goldQuantityChi=input_data.gold_quantity_chi,
            goldPricePerChi=input_data.gold_price_per_chi,
            isActive=input_data.is_active,
            note=input_data.note.strip(),
        )
        return self._repo.update_source(code, source)

    def list(self) -> list[Source]:
        return self._repo.list_sources()


def normalize_code(value: str) -> str:
    return value.strip().replace(" ", "_")


def resolve_actual_balance(kind: str, actual_balance: int, gold_quantity_chi: float, gold_price_per_chi: int) -> int:
    if kind == "gold":
        return int(round(gold_quantity_chi * gold_price_per_chi))
    return actual_balance
