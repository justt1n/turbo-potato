from pathlib import Path

from app.core.config import load_settings, reset_settings_cache


def test_load_settings_defaults(monkeypatch) -> None:
    monkeypatch.delenv("APP_CONFIG_FILE", raising=False)
    monkeypatch.delenv("APP_PORT", raising=False)
    reset_settings_cache()

    settings = load_settings()

    assert settings.app.env == "development"
    assert settings.app.port == "8080"
    assert settings.app.timezone == "UTC"


def test_load_settings_from_yaml_and_files(tmp_path: Path, monkeypatch) -> None:
    prompt_file = tmp_path / "prompt.txt"
    prompt_file.write_text("prompt body\n", encoding="utf-8")

    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        f"""
app:
  env: production
  port: "9000"
  timezone: Asia/Ho_Chi_Minh
ai:
  provider: openai
  model: gpt-5-mini
  prompt_file: {prompt_file}
""".strip(),
        encoding="utf-8",
    )

    monkeypatch.setenv("APP_CONFIG_FILE", str(config_file))
    reset_settings_cache()

    settings = load_settings()

    assert settings.app.env == "production"
    assert settings.app.port == "9000"
    assert settings.app.timezone == "Asia/Ho_Chi_Minh"
    assert settings.ai.prompt == "prompt body"


def test_prompt_file_overrides_inline_prompt(tmp_path: Path, monkeypatch) -> None:
    prompt_file = tmp_path / "parser.txt"
    prompt_file.write_text("file prompt wins\n", encoding="utf-8")

    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        f"""
ai:
  provider: gemini
  model: gemma-3-27b-it
  prompt: inline prompt should not win
  prompt_file: {prompt_file}
""".strip(),
        encoding="utf-8",
    )

    monkeypatch.setenv("APP_CONFIG_FILE", str(config_file))
    reset_settings_cache()

    settings = load_settings()

    assert settings.ai.prompt == "file prompt wins"


def test_use_google_sheets_false_when_config_incomplete() -> None:
    settings = load_settings()

    assert settings.use_google_sheets() is False


def test_load_settings_reads_service_account_file(tmp_path: Path, monkeypatch) -> None:
    service_account_file = tmp_path / "service-account.json"
    service_account_file.write_text('{"client_email":"robot@example.test","private_key":"key","token_uri":"https://oauth.example.test/token"}', encoding="utf-8")

    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        f"""
sheets:
  spreadsheet_id: sheet-id
  service_account_file: {service_account_file}
""".strip(),
        encoding="utf-8",
    )

    monkeypatch.setenv("APP_CONFIG_FILE", str(config_file))
    reset_settings_cache()

    settings = load_settings()

    assert settings.use_google_sheets() is True
    assert settings.sheets.service_account_json.startswith('{"client_email"')
