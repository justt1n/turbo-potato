from __future__ import annotations

from functools import lru_cache

from app.ai.client import AIClient, build_ai_client
from app.core.config import Settings, get_settings
from app.core.runtime import Clock, TransactionIDGenerator
from app.domain.assets.service import AssetsService
from app.domain.jars.service import JarService
from app.domain.goals.service import GoalService
from app.domain.integrations.google_chat import GoogleChatService
from app.domain.ingestion.service import IngestionService
from app.domain.ingestion.review_service import ParsedReceiptReviewService
from app.domain.metrics.service import MetricsService
from app.domain.migrations.service import LegacyJarMigrationService
from app.domain.reports.service import ReportsService
from app.domain.rules.service import RulesService
from app.domain.sources.service import SourceService
from app.domain.transactions.service import TransactionService
from app.infrastructure.memory.repositories import (
    MemoryAuditLogger,
    MemoryJarsRepository,
    MemoryGoalsRepository,
    MemoryParsedReceiptsRepository,
    MemoryReportsRepository,
    MemoryRulesRepository,
    MemorySourcesRepository,
    MemoryTransactionRepository,
)
from app.infrastructure.sheets.bootstrap import NoopBootstrapper, SpreadsheetBootstrapper
from app.infrastructure.sheets.client import GoogleValuesClient
from app.infrastructure.sheets.repositories import (
    GoogleAuditLogger,
    GoogleJarsRepository,
    GoogleGoalsRepository,
    GoogleParsedReceiptsRepository,
    GoogleReportsRepository,
    GoogleRulesRepository,
    GoogleSourcesRepository,
    GoogleTransactionRepository,
)
from app.infrastructure.sheets.types import Bootstrapper


@lru_cache(maxsize=1)
def get_clock() -> Clock:
    return Clock()


@lru_cache(maxsize=1)
def get_transaction_id_generator() -> TransactionIDGenerator:
    return TransactionIDGenerator()


@lru_cache(maxsize=1)
def get_ai_client() -> AIClient:
    return build_ai_client(get_settings())


@lru_cache(maxsize=1)
def get_google_sheets_client() -> GoogleValuesClient:
    return GoogleValuesClient.from_settings(get_settings())


@lru_cache(maxsize=1)
def get_bootstrapper() -> Bootstrapper:
    settings = get_settings()
    if not settings.use_google_sheets():
        return NoopBootstrapper()
    client = get_google_sheets_client()
    return SpreadsheetBootstrapper(client, client, settings.sheets.spreadsheet_id)


@lru_cache(maxsize=1)
def get_transaction_repository():
    settings = get_settings()
    if not settings.use_google_sheets():
        return MemoryTransactionRepository()
    return GoogleTransactionRepository(get_google_sheets_client(), settings.sheets.spreadsheet_id)


@lru_cache(maxsize=1)
def get_audit_logger():
    settings = get_settings()
    if not settings.use_google_sheets():
        return MemoryAuditLogger()
    return GoogleAuditLogger(get_google_sheets_client(), settings.sheets.spreadsheet_id)


@lru_cache(maxsize=1)
def get_goals_repository():
    settings = get_settings()
    if not settings.use_google_sheets():
        return MemoryGoalsRepository()
    return GoogleGoalsRepository(get_google_sheets_client(), settings.sheets.spreadsheet_id)


@lru_cache(maxsize=1)
def get_jars_repository():
    settings = get_settings()
    if not settings.use_google_sheets():
        return MemoryJarsRepository()
    return GoogleJarsRepository(get_google_sheets_client(), settings.sheets.spreadsheet_id)


@lru_cache(maxsize=1)
def get_rules_repository():
    settings = get_settings()
    if not settings.use_google_sheets():
        return MemoryRulesRepository()
    return GoogleRulesRepository(get_google_sheets_client(), settings.sheets.spreadsheet_id)


@lru_cache(maxsize=1)
def get_sources_repository():
    settings = get_settings()
    if not settings.use_google_sheets():
        return MemorySourcesRepository()
    return GoogleSourcesRepository(get_google_sheets_client(), settings.sheets.spreadsheet_id)


@lru_cache(maxsize=1)
def get_parsed_receipts_repository():
    settings = get_settings()
    if not settings.use_google_sheets():
        return MemoryParsedReceiptsRepository()
    return GoogleParsedReceiptsRepository(get_google_sheets_client(), settings.sheets.spreadsheet_id)


@lru_cache(maxsize=1)
def get_reports_repository():
    settings = get_settings()
    if not settings.use_google_sheets():
        return MemoryReportsRepository()
    return GoogleReportsRepository(get_google_sheets_client(), settings.sheets.spreadsheet_id)


@lru_cache(maxsize=1)
def get_transaction_service() -> TransactionService:
    return TransactionService(get_transaction_repository(), get_audit_logger(), get_transaction_id_generator(), get_clock())


@lru_cache(maxsize=1)
def get_goals_service() -> GoalService:
    return GoalService(get_goals_repository(), get_clock())


@lru_cache(maxsize=1)
def get_jars_service() -> JarService:
    return JarService(get_jars_repository())


@lru_cache(maxsize=1)
def get_rules_service() -> RulesService:
    return RulesService(get_rules_repository())


@lru_cache(maxsize=1)
def get_sources_service() -> SourceService:
    return SourceService(get_sources_repository())


@lru_cache(maxsize=1)
def get_metrics_service() -> MetricsService:
    return MetricsService(get_transaction_service(), get_goals_service(), get_rules_service(), get_sources_service(), get_clock())


@lru_cache(maxsize=1)
def get_assets_service() -> AssetsService:
    return AssetsService(get_transaction_service(), get_sources_service())


@lru_cache(maxsize=1)
def get_legacy_jar_migration_service() -> LegacyJarMigrationService:
    return LegacyJarMigrationService(get_jars_service(), get_sources_service())


def _prompt_source(settings: Settings) -> str:
    if settings.ai.prompt_file:
        return settings.ai.prompt_file
    if settings.ai.prompt:
        return "inline-config"
    return "default"


def _report_prompt_source(settings: Settings, monthly: bool) -> str:
    if monthly:
        if settings.ai.monthly_report_prompt_file:
            return settings.ai.monthly_report_prompt_file
        if settings.ai.monthly_report_prompt:
            return "inline-config"
        return "default"
    if settings.ai.daily_report_prompt_file:
        return settings.ai.daily_report_prompt_file
    if settings.ai.daily_report_prompt:
        return "inline-config"
    return "default"


@lru_cache(maxsize=1)
def get_ingestion_service() -> IngestionService:
    settings = get_settings()
    return IngestionService(
        get_transaction_service(),
        get_parsed_receipts_repository(),
        get_ai_client(),
        get_clock(),
        settings.ai.model,
        settings.ai.prompt,
        _prompt_source(settings),
    )


@lru_cache(maxsize=1)
def get_reports_service() -> ReportsService:
    settings = get_settings()
    return ReportsService(
        get_reports_repository(),
        get_metrics_service(),
        get_transaction_service(),
        get_goals_service(),
        get_rules_service(),
        get_ai_client(),
        get_clock(),
        settings.app.timezone,
        settings.ai.model,
        settings.ai.daily_report_prompt,
        settings.ai.monthly_report_prompt,
        _report_prompt_source(settings, monthly=False),
        _report_prompt_source(settings, monthly=True),
    )


@lru_cache(maxsize=1)
def get_parsed_receipt_review_service() -> ParsedReceiptReviewService:
    return ParsedReceiptReviewService(get_parsed_receipts_repository(), get_transaction_service())


@lru_cache(maxsize=1)
def get_google_chat_service() -> GoogleChatService:
    return GoogleChatService(get_ingestion_service())


def reset_dependency_caches() -> None:
    get_clock.cache_clear()
    get_transaction_id_generator.cache_clear()
    get_ai_client.cache_clear()
    get_google_sheets_client.cache_clear()
    get_bootstrapper.cache_clear()
    get_transaction_repository.cache_clear()
    get_audit_logger.cache_clear()
    get_goals_repository.cache_clear()
    get_jars_repository.cache_clear()
    get_rules_repository.cache_clear()
    get_sources_repository.cache_clear()
    get_parsed_receipts_repository.cache_clear()
    get_reports_repository.cache_clear()
    get_transaction_service.cache_clear()
    get_goals_service.cache_clear()
    get_jars_service.cache_clear()
    get_rules_service.cache_clear()
    get_sources_service.cache_clear()
    get_metrics_service.cache_clear()
    get_assets_service.cache_clear()
    get_legacy_jar_migration_service.cache_clear()
    get_ingestion_service.cache_clear()
    get_reports_service.cache_clear()
    get_parsed_receipt_review_service.cache_clear()
    get_google_chat_service.cache_clear()
