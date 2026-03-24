from __future__ import annotations

from typing import Protocol

from app.domain.jars.model import Jar
from app.domain.migrations.model import MigrationItem, MigrationResult
from app.domain.sources.model import CreateInput, Source


class JarsReader(Protocol):
    def list(self) -> list[Jar]: ...


class SourcesManager(Protocol):
    def list(self) -> list[Source]: ...

    def create(self, input_data: CreateInput) -> Source: ...


class LegacyJarMigrationService:
    def __init__(self, jars: JarsReader, sources: SourcesManager) -> None:
        self._jars = jars
        self._sources = sources

    def migrate_legacy_jars(self, dry_run: bool = False) -> MigrationResult:
        existing_source_codes = {item.code for item in self._sources.list()}
        items: list[MigrationItem] = []
        candidates = 0
        created = 0
        skipped = 0

        for jar in self._jars.list():
            if not looks_like_legacy_asset_jar(jar):
                continue

            candidates += 1
            source_code = jar.code
            if source_code in existing_source_codes:
                skipped += 1
                items.append(
                    MigrationItem(
                        jarCode=jar.code,
                        jarName=jar.name,
                        sourceCode=source_code,
                        status="skipped",
                        reason="source already exists",
                    )
                )
                continue

            if dry_run:
                items.append(
                    MigrationItem(
                        jarCode=jar.code,
                        jarName=jar.name,
                        sourceCode=source_code,
                        status="would_create",
                        reason="eligible legacy jar",
                    )
                )
                continue

            self._sources.create(
                CreateInput(
                    code=source_code,
                    name=jar.name,
                    kind=map_legacy_kind(jar.kind),
                    provider="",
                    linkedJarCode="",
                    openingBalance=jar.opening_balance,
                    actualBalance=jar.actual_balance,
                    goldQuantityChi=0,
                    goldPricePerChi=0,
                    isActive=jar.is_active,
                    note=merge_note(jar.note),
                )
            )
            existing_source_codes.add(source_code)
            created += 1
            items.append(
                MigrationItem(
                    jarCode=jar.code,
                    jarName=jar.name,
                    sourceCode=source_code,
                    status="created",
                    reason="migrated to sources",
                )
            )

        return MigrationResult(
            dryRun=dry_run,
            candidates=candidates,
            created=created,
            skipped=skipped,
            items=items,
        )


def looks_like_legacy_asset_jar(jar: Jar) -> bool:
    kind = jar.kind.strip().lower()
    return kind != "bucket" or jar.opening_balance > 0 or jar.actual_balance > 0


def map_legacy_kind(value: str) -> str:
    kind = value.strip().lower()
    if kind in {"bank", "bank_account"}:
        return "bank_account"
    if kind == "wallet":
        return "wallet"
    if kind in {"cash", "cash_box"}:
        return "cash_box"
    if kind == "reserve_cash":
        return "reserve_cash"
    if kind == "gold":
        return "gold"
    return "other"


def merge_note(note: str) -> str:
    cleaned = note.strip()
    migration_note = "Migrated from legacy jar"
    if not cleaned:
        return migration_note
    return f"{cleaned} | {migration_note}"
