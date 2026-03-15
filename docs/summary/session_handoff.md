# Session Handoff

This file should be updated whenever implementation changes, so it remains the single handoff source for the next session.

## Current state

This repo is no longer docs-only. It now has a working `backend/` and `frontend/` foundation with tests and CI.

Project direction:

- frontend: Vue 3 + TypeScript + Vite
- backend current implementation: Python + FastAPI
- archived backend reference: Go + Fiber in `backend_go_archive/`
- storage for v1: Google Sheets
- backend owns business logic and metrics
- frontend renders backend-driven metrics

Main architecture docs:

- `docs/architecture/grand_design.md`
- `docs/architecture/vue_implementation_plan.md`
- `docs/architecture/implementation_roadmap.md`
- `docs/summary/python_fastapi_migration_plan.md`
- `docs/summary/start_guide.md`

Legacy requirement docs remain under:

- `docs/legacy/requirements/`

## Backend status

### Migration direction

Backend direction has changed:

- `backend/` is now the Python backend
- `backend_go_archive/` contains the previous Go implementation
- future backend continuation should happen in Python
- the Go code remains useful as a parity reference while Python is still catching up

Migration plan:

- `docs/summary/python_fastapi_migration_plan.md`

### Implemented

Python scaffold:

- FastAPI app bootstrap in `backend/app/main.py`
- Health route in `backend/app/api/routes/health.py`
- YAML + env config loader in `backend/app/core/config.py`
- AI client layer in `backend/app/ai/client.py`
  - supports `openai`, `gemini/google`, and `ollama`
  - recommended hosted Gemma path is Google API with `provider: gemini` and model `gemma-3-27b-it`
  - prompt workflow is file-first through `.txt` prompt files
  - when both inline prompt text and a prompt file are set, the file wins
- Google Sheets client in `backend/app/infrastructure/sheets/client.py`
- Spreadsheet bootstrap in `backend/app/infrastructure/sheets/bootstrap.py`
- dependency wiring in `backend/app/core/dependencies.py`
- transaction, goal, rule, metrics, ingestion, and reports domain services in `backend/app/domain/`
- route parity layer in `backend/app/api/routes/app_routes.py`
- Google Sheets and memory repositories in `backend/app/infrastructure/`
- Local virtualenv workflow in `backend/.venv`
- Python packaging and test config in `backend/pyproject.toml`
- Docker packaging:
  - `backend/Dockerfile`
  - `frontend/Dockerfile`
  - `frontend/nginx.conf`
  - `docker-compose.yml`

Example runtime config:

- `config/app.example.yaml`
- local machine template:
  - `config/local.yaml`
  - local config files are gitignored

Prompt editing guide:

- `prompts/README.md`
- startup guide:
  - `docs/summary/start_guide.md`

Default prompt file:

- `prompts/chat_parser.default.txt`
- `prompts/daily_report.default.txt`
- `prompts/monthly_report.default.txt`
- prompt defaults now explicitly support Vietnamese
- parser prompt now assumes Google Chat is the most common message source

Current Python feature coverage:

- most core backend behavior is now implemented in Python
- current live route parity:
  - `GET /api/v1/health`
  - `POST /api/v1/admin/bootstrap`
  - `GET /api/v1/dashboard/summary`
  - `GET /api/v1/dashboard/reports`
  - `POST /api/v1/dashboard/reports/monthly`
  - `GET /api/v1/transactions`
  - `POST /api/v1/transactions`
  - `POST /api/v1/transactions/{id}/correct`
  - `POST /api/v1/transactions/{id}/undo`
  - `GET /api/v1/goals`
  - `POST /api/v1/goals`
  - `GET /api/v1/fixed-cost-rules`
  - `POST /api/v1/fixed-cost-rules`
  - `POST /api/v1/ingestion/chat`
  - `GET /api/v1/parsed-receipts`
  - `GET /api/v1/parsed-receipts/{receipt_id}`
  - `POST /api/v1/parsed-receipts/{receipt_id}/confirm`
  - `POST /api/v1/parsed-receipts/{receipt_id}/correct`
  - `POST /api/v1/parsed-receipts/{receipt_id}/undo`
- config parity started:
  - `app.env`
  - `app.port`
  - `app.timezone`
  - `sheets.*`
  - `ai.*`
- LLM parsing behavior:
  - prompt text is editable from config
  - ingestion and report parsing extract JSON via regex from the model response
  - parsing no longer relies on `find("{")` / `rfind("}")`
- tests exist and pass for:
  - AI client behavior
  - API route behavior
  - config loading
  - core domain behavior
  - health endpoint
  - Sheets client behavior
  - Sheets bootstrap behavior

Archived Go reference:

- all previous business logic still exists in `backend_go_archive/`
- use it as the source when porting:
  - transactions
  - goals
  - rules
  - metrics
  - ingestion
  - reports
  - Sheets adapters
  - AI adapters

### Implemented endpoints

Python backend:

- `GET /api/v1/health`
- `POST /api/v1/admin/bootstrap`
- `GET /api/v1/dashboard/summary`
- `GET /api/v1/dashboard/reports`
- `POST /api/v1/dashboard/reports/monthly`
- `GET /api/v1/transactions`
- `POST /api/v1/transactions`
- `POST /api/v1/transactions/{id}/correct`
- `POST /api/v1/transactions/{id}/undo`
- `GET /api/v1/goals`
- `POST /api/v1/goals`
- `GET /api/v1/fixed-cost-rules`
- `POST /api/v1/fixed-cost-rules`
- `POST /api/v1/ingestion/chat`
- `GET /api/v1/parsed-receipts`
- `GET /api/v1/parsed-receipts/{receipt_id}`
- `POST /api/v1/parsed-receipts/{receipt_id}/confirm`
- `POST /api/v1/parsed-receipts/{receipt_id}/correct`
- `POST /api/v1/parsed-receipts/{receipt_id}/undo`

### What is still missing on backend

Most important missing backend piece in Python:

- richer end-to-end validation against real Google API + Sheets config, plus deeper review editing UX

Recommended next backend step:

1. Do a live local run with Google AI API using `gemma-3-27b-it` and validate prompt quality for ingestion and reports.
2. Do a real Google Sheets integration verification pass.
3. Add a richer correction UI on the Review page beyond confirm/revert.
4. Consider splitting the large unified route file as feature work resumes.

Other backend gaps:

- no auth/security layer yet
- no full inline correction editor in the UI yet
- no live Google Sheets integration test yet
- no deploy workflow yet that pushes images or deploys to a target environment

## Frontend status

### Implemented

App shell and theme:

- `frontend/src/app/App.vue`
- `frontend/src/app/theme.ts`
- `frontend/src/styles.css`

Theme system:

- palette tokens are centralized
- palette can be changed later without rewriting components

Dashboard UI:

- `frontend/src/features/dashboard/DashboardPage.vue`
- `frontend/src/components/MetricRing.vue`
- `frontend/src/components/BaselineMonitor.vue`

Dashboard now uses real backend API:

- `frontend/src/api/dashboard.ts`
- fetches `GET /api/v1/dashboard/summary`
- fetches `GET /api/v1/dashboard/reports`
- renders backend-driven STS, anomaly, goal pace, posture, baselines
- renders backend-driven daily report and monthly report
- supports manual monthly report generation from the dashboard

Transactions page:

- `frontend/src/features/transactions/TransactionsPage.vue`
- manual create + list flow exists
- uses:
  - `frontend/src/api/transactions.ts`
  - `frontend/src/api/http.ts`

Placeholder pages still basic:

- `frontend/src/features/goals/GoalsPage.vue`
- `frontend/src/features/settings/SettingsPage.vue`

Review page:

- `frontend/src/features/review/ReviewPage.vue`
- now fetches `GET /api/v1/parsed-receipts`
- renders parsed receipt cards, linked draft transaction info, and prompt/LLM payload context
- supports confirm and revert actions for draft receipts
- supports inline correction editing for amount, jar, goal, account, note, and fixed-cost flag before saving

### What is still missing on frontend

Recommended next frontend step:

- polish the review editor UX with better defaults, validation hints, and maybe quick-fill actions from regex/LLM suggestions

If choosing frontend work before LLM work:

- connect `GoalsPage` to `GET/POST /api/v1/goals`
- add fixed-cost rule management to `SettingsPage`
- refresh dashboard after transaction/goal changes

## Tests

Python backend tests:

- `backend/tests/test_ai_client.py`
- `backend/tests/test_api_routes.py`
- `backend/tests/test_config.py`
- `backend/tests/test_domain_services.py`
- `backend/tests/test_health.py`
- `backend/tests/test_sheets_client.py`
- `backend/tests/test_sheets_bootstrap.py`

Recent verification additions:

- parsed receipt list/detail API coverage
- parsed receipt review service coverage
- parsed receipt confirm/undo API coverage
- ollama AI client coverage
- regex-based JSON extraction coverage for ingestion and reports

Archived Go backend tests remain in:

- `backend_go_archive/test/app`
- `backend_go_archive/test/config`
- `backend_go_archive/test/domain`
- `backend_go_archive/test/http`
- `backend_go_archive/test/sheets`

Frontend tests:

- `frontend/src/lib/chart.test.ts`
- `frontend/src/lib/formatCurrency.test.ts`

## Verification status

These have passed during this session:

- backend: `.venv/bin/python -m pytest`
- frontend: `npm test`
- frontend: `npm run build`

## Config notes

Local real config is optional right now.

Why:

- backend falls back to memory mode when Sheets config is absent
- dashboard and transaction flows can still run locally in memory

Real config becomes required when:

- using real Google Sheets persistence
- using real AI provider credentials for ingestion or reports

Expected local files when ready:

- `config/local.yaml`
- `secrets/google-service-account.json`
- `secrets/google-ai-api-key.txt`

Important config keys now:

- `app.timezone`
- `ai.provider`
- `ai.base_url`
- `ai.model`
- `ai.prompt_file`
- `ai.daily_report_prompt_file`
- `ai.monthly_report_prompt_file`

## Important implementation decisions already made

- Google Sheets is v1 source of record
- backend is the source of truth for metrics
- frontend does not calculate metrics itself
- prompt must be configurable, not hardcoded
- prompt editing should happen in `.txt` prompt files first, not inline YAML
- prompt defaults should explicitly support Vietnamese input/output where relevant
- tests live under `backend/tests/`
- config is YAML, not JSON
- hosted Gemma should use Google AI API with `provider: gemini` and model `gemma-3-27b-it`
- LLM responses should be treated as text blobs and JSON should be extracted with regex before parsing

## Recommended next step

Best next step:

Run the Python backend against real Google AI API + Google Sheets config, then improve inline correction on the Review page.

Reason:

- the core frontend-used parity routes now exist in Python
- review confirm/revert is now working, so the main remaining risk is real-provider behavior
- `gemma-3-27b-it` prompt quality should be validated before more product logic is built on top

Suggested order:

1. Create `config/local.yaml` with Google Sheets and Google AI API credentials.
2. Run ingestion and dashboard reports against `provider: gemini` with model `gemma-3-27b-it`.
3. Tune prompts if Gemma returns weak JSON or too much prose around the JSON block.
4. Refine the inline correction workflow in `ReviewPage` after real usage feedback.
5. Add a live integration verification note to this handoff file.

## Quick file map for continuation

Migration guide:

- `docs/summary/python_fastapi_migration_plan.md`

Backend core:

- `backend/app/main.py`
- `backend/app/core/config.py`
- `backend/app/core/dependencies.py`
- `backend/app/api/routes/health.py`
- `backend/app/api/routes/app_routes.py`
- `backend/app/ai/client.py`
- `backend/app/infrastructure/sheets/client.py`
- `backend/app/infrastructure/sheets/bootstrap.py`
- `backend/app/domain/`
- `backend/app/infrastructure/memory/repositories.py`
- `backend/app/infrastructure/sheets/repositories.py`

Python tests:

- `backend/tests/test_ai_client.py`
- `backend/tests/test_api_routes.py`
- `backend/tests/test_config.py`
- `backend/tests/test_domain_services.py`
- `backend/tests/test_health.py`
- `backend/tests/test_sheets_client.py`
- `backend/tests/test_sheets_bootstrap.py`

Go archive reference:

- `backend_go_archive/internal/config/config.go`
- `backend_go_archive/internal/app/app.go`
- `backend_go_archive/internal/http/transactions.go`
- `backend_go_archive/internal/domain/transactions/`
- `backend_go_archive/internal/domain/goals/`
- `backend_go_archive/internal/domain/rules/`
- `backend_go_archive/internal/domain/metrics/`
- `backend_go_archive/internal/domain/ingestion/`
- `backend_go_archive/internal/domain/reports/`
- `backend_go_archive/internal/sheets/`
- `backend_go_archive/internal/ai/client.go`

Frontend dashboard:

- `frontend/src/api/dashboard.ts`
- `frontend/src/features/dashboard/DashboardPage.vue`
- `frontend/src/components/MetricRing.vue`
- `frontend/src/components/BaselineMonitor.vue`

Config/prompt:

- `config/app.example.yaml`
- `backend/internal/ai/client.go`
- `prompts/chat_parser.default.txt`
- `prompts/daily_report.default.txt`
- `prompts/monthly_report.default.txt`

## AI provider notes

Current provider support in `backend/internal/ai/client.go`:

- `openai`
  - uses `POST /v1/responses`
- `gemini`
  - uses `POST /v1beta/models/{model}:generateContent`

Config behavior:

- if `ai.provider` is empty or `ai.api_key` is missing, the app uses `NoopClient`
- `ai.base_url` is optional and mainly useful for testing or proxies

Current runtime behavior:

- ingestion uses AI when configured, otherwise falls back cleanly
- reports use AI when configured, otherwise fall back to deterministic summaries
