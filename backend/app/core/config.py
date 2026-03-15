from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class AppConfig(BaseModel):
    env: str = "development"
    port: str = "8080"
    timezone: str = "UTC"


class SheetsConfig(BaseModel):
    spreadsheet_id: str = ""
    service_account_json: str = ""
    service_account_file: str = ""


class AIConfig(BaseModel):
    provider: str = ""
    base_url: str = ""
    api_key: str = ""
    api_key_file: str = ""
    model: str = ""
    prompt: str = ""
    prompt_file: str = ""
    daily_report_prompt: str = ""
    daily_report_prompt_file: str = ""
    monthly_report_prompt: str = ""
    monthly_report_prompt_file: str = ""


class Settings(BaseModel):
    app: AppConfig = Field(default_factory=AppConfig)
    sheets: SheetsConfig = Field(default_factory=SheetsConfig)
    ai: AIConfig = Field(default_factory=AIConfig)

    def use_google_sheets(self) -> bool:
        return bool(self.sheets.spreadsheet_id and self.sheets.service_account_json)


def _read_text(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def _merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _apply_env(data: dict[str, Any]) -> dict[str, Any]:
    app = dict(data.get("app", {}))
    sheets = dict(data.get("sheets", {}))
    ai = dict(data.get("ai", {}))

    app["env"] = os.getenv("APP_ENV", app.get("env", "development"))
    app["port"] = os.getenv("APP_PORT", app.get("port", "8080"))
    app["timezone"] = os.getenv("APP_TIMEZONE", app.get("timezone", "UTC"))

    sheets["spreadsheet_id"] = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID", sheets.get("spreadsheet_id", ""))
    sheets["service_account_json"] = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", sheets.get("service_account_json", ""))
    sheets["service_account_file"] = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", sheets.get("service_account_file", ""))

    ai["provider"] = os.getenv("AI_PROVIDER", ai.get("provider", ""))
    ai["base_url"] = os.getenv("AI_BASE_URL", ai.get("base_url", ""))
    ai["api_key"] = os.getenv("AI_API_KEY", ai.get("api_key", ""))
    ai["api_key_file"] = os.getenv("AI_API_KEY_FILE", ai.get("api_key_file", ""))
    ai["model"] = os.getenv("AI_MODEL", ai.get("model", ""))
    ai["prompt"] = os.getenv("AI_PROMPT", ai.get("prompt", ""))
    ai["prompt_file"] = os.getenv("AI_PROMPT_FILE", ai.get("prompt_file", ""))
    ai["daily_report_prompt"] = os.getenv("AI_DAILY_REPORT_PROMPT", ai.get("daily_report_prompt", ""))
    ai["daily_report_prompt_file"] = os.getenv("AI_DAILY_REPORT_PROMPT_FILE", ai.get("daily_report_prompt_file", ""))
    ai["monthly_report_prompt"] = os.getenv("AI_MONTHLY_REPORT_PROMPT", ai.get("monthly_report_prompt", ""))
    ai["monthly_report_prompt_file"] = os.getenv("AI_MONTHLY_REPORT_PROMPT_FILE", ai.get("monthly_report_prompt_file", ""))

    return {"app": app, "sheets": sheets, "ai": ai}


def load_settings() -> Settings:
    data: dict[str, Any] = {}
    config_file = os.getenv("APP_CONFIG_FILE", "").strip()
    if config_file:
        loaded = yaml.safe_load(Path(config_file).read_text(encoding="utf-8")) or {}
        if not isinstance(loaded, dict):
            raise ValueError("config file must contain a YAML object")
        data = _merge(data, loaded)

    data = _apply_env(data)
    settings = Settings.model_validate(data)

    if not settings.app.port:
        raise ValueError("app.port is required")

    if not settings.sheets.service_account_json and settings.sheets.service_account_file:
        settings.sheets.service_account_json = _read_text(settings.sheets.service_account_file)

    if not settings.ai.api_key and settings.ai.api_key_file:
        settings.ai.api_key = _read_text(settings.ai.api_key_file).strip()

    if settings.ai.prompt_file:
        settings.ai.prompt = _read_text(settings.ai.prompt_file).strip()

    if settings.ai.daily_report_prompt_file:
        settings.ai.daily_report_prompt = _read_text(settings.ai.daily_report_prompt_file).strip()

    if settings.ai.monthly_report_prompt_file:
        settings.ai.monthly_report_prompt = _read_text(settings.ai.monthly_report_prompt_file).strip()

    return settings


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return load_settings()


def reset_settings_cache() -> None:
    get_settings.cache_clear()
