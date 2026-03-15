# Python FastAPI Migration Plan

## Goal

Migrate the backend from `Go + Fiber` to `Python + FastAPI` while preserving:

- current frontend API contracts as much as possible
- Google Sheets as v1 source of record
- config-driven prompts and credentials
- current metrics, ingestion, and reporting behavior
- hosted Gemma via Google AI API where desired

The frontend should need minimal changes during the migration.

## Current progress

Completed:

- Phase 1 scaffold is done
- Phase 2 infrastructure foundation is done for:
  - AI client layer
  - Google Sheets client
  - spreadsheet bootstrap
  - dependency wiring
- Phase 3 core parity is largely done for:
  - transactions
  - goals
  - fixed-cost rules
  - metrics
  - ingestion
  - reports
  - parsed receipt read/review endpoints
  - API route parity for the current frontend-used endpoints
- `backend/` now contains the Python FastAPI scaffold
- `backend_go_archive/` keeps the previous Go backend as reference
- Python tests currently pass for:
  - health route
  - config loading
  - AI clients
  - API routes
  - core domain services
  - Sheets client
  - Sheets bootstrap

Next active phase:

- Phase 4 review actions and parity hardening

Preferred LLM path for the next phase:

- use Google AI API with `provider: gemini`
- use hosted Gemma model `gemma-3-27b-it`
- keep prompt/config surface provider-agnostic so OpenAI or Ollama can still be swapped in later

## Migration strategy

Do not keep building major new backend features in Go.

From this point, backend continuation should follow this order:

1. Scaffold the Python backend.
2. Recreate current Go behavior module by module.
3. Run the frontend against the Python API.
4. Retire the Go backend only after Python reaches feature parity.

Recommended approach:

- keep `frontend/` unchanged initially
- preserve the existing route shapes under `/api/v1/...`
- use `backend_go_archive/` as the reference behavior during migration

## Target stack

Recommended Python stack:

- `FastAPI`
- `Pydantic v2`
- `uv` or `poetry` for dependency management
- `httpx` for outbound HTTP
- `pytest`
- `ruff`
- `mypy`

Optional but recommended:

- `pydantic-settings` for config loading
- `tenacity` for retry logic

## Target backend layout

Suggested Python structure:

```text
backend_py/
  pyproject.toml
  app/
    main.py
    api/
      routes/
        health.py
        dashboard.py
        transactions.py
        goals.py
        fixed_cost_rules.py
        ingestion.py
        parsed_receipts.py
    core/
      config.py
      dependencies.py
      clock.py
      ids.py
    domain/
      transactions/
      goals/
      rules/
      metrics/
      ingestion/
      reports/
    infrastructure/
      sheets/
        client.py
        bootstrap.py
        transactions_repo.py
        goals_repo.py
        rules_repo.py
        parsed_receipts_repo.py
        reports_repo.py
      ai/
        client.py
        openai_client.py
        gemini_client.py
      memory/
        transactions_repo.py
        goals_repo.py
        rules_repo.py
        parsed_receipts_repo.py
        reports_repo.py
    schemas/
      transactions.py
      goals.py
      rules.py
      dashboard.py
      ingestion.py
      reports.py
  tests/
    api/
    domain/
    infrastructure/
```

## Parity scope

The Python backend should reach parity with these existing Go capabilities first.

### Config parity

Current behavior to preserve:

- YAML config file
- env override support
- secret file support
- prompt file support
- Sheets optional
- AI optional

Must support these keys:

- `app.env`
- `app.port`
- `app.timezone`
- `sheets.spreadsheet_id`
- `sheets.service_account_file`
- `sheets.service_account_json`
- `ai.provider`
- `ai.base_url`
- `ai.api_key`
- `ai.api_key_file`
- `ai.model`
- `ai.prompt`
- `ai.prompt_file`
- `ai.daily_report_prompt`
- `ai.daily_report_prompt_file`
- `ai.monthly_report_prompt`
- `ai.monthly_report_prompt_file`

Recommended live config for current work:

- `ai.provider: gemini`
- `ai.base_url: https://generativelanguage.googleapis.com`
- `ai.model: gemma-3-27b-it`
- `ai.api_key_file: ./secrets/google-ai-api-key.txt`

### API parity

Current routes to preserve:

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

Add after parity:

- parsed receipt confirm/correct actions from the review flow
- optional parsed receipt delete/archive behavior if the workflow needs it

### Domain parity

Modules to port:

- transactions
- goals
- rules
- metrics
- ingestion
- reports

### Storage parity

Need both:

- Google Sheets repositories
- in-memory fallback repositories

## Go to Python mapping

Use the current Go files as behavioral references.

Reference map:

- config:
  - `backend/internal/config/config.go`
- app wiring:
  - `backend/internal/app/app.go`
- routes:
  - `backend/internal/http/transactions.go`
- transactions:
  - `backend/internal/domain/transactions/service.go`
- goals:
  - `backend/internal/domain/goals/service.go`
- rules:
  - `backend/internal/domain/rules/service.go`
- metrics:
  - `backend/internal/domain/metrics/service.go`
  - `backend/internal/domain/metrics/model.go`
- ingestion:
  - `backend/internal/domain/ingestion/service.go`
  - `backend/internal/domain/ingestion/model.go`
- reports:
  - `backend/internal/domain/reports/service.go`
  - `backend/internal/domain/reports/model.go`
- AI:
  - `backend/internal/ai/client.go`
- Sheets:
  - `backend/internal/sheets/google_client.go`
  - `backend/internal/sheets/bootstrap.go`
  - repository files under `backend/internal/sheets/`

## Implementation phases

### Phase 0: Freeze and baseline

Goal:

- treat the Go backend as the reference implementation

Tasks:

- stop adding major new features to Go
- keep updating docs and prompts only if needed
- use current Go tests and endpoint behavior as migration reference

Done when:

- migration starts from a stable Go baseline

### Phase 1: Python scaffold

Goal:

- create the Python backend foundation

Tasks:

- create `backend_py/`
- add `pyproject.toml`
- add FastAPI app bootstrap
- add config loading
- add dependency injection setup
- add test, lint, and type-check tooling
- add `.env` / config conventions matching current YAML approach

Done when:

- Python app can start
- `GET /api/v1/health` works
- tests run

Status:

- completed

### Phase 2: Infrastructure parity

Goal:

- rebuild shared runtime infrastructure

Tasks:

- Google Sheets HTTP client
- service account auth
- spreadsheet bootstrap
- memory fallback repositories
- AI client layer:
  - OpenAI
  - Gemini

Done when:

- Sheets bootstrapping works from Python
- AI client can produce text with the same config keys

### Phase 3: Transactions, goals, rules

Goal:

- port the CRUD backbone first

Tasks:

- transactions domain/service/repository
- goals domain/service/repository
- fixed-cost rules domain/service/repository
- matching routes and schemas

Done when:

- frontend transaction and goal flows can hit Python instead of Go

### Phase 4: Metrics parity

Goal:

- port dashboard summary logic exactly

Tasks:

- STS
- anomaly
- goal pace
- operating posture
- baseline series
- `GET /api/v1/dashboard/summary`

Done when:

- dashboard renders against Python with no frontend changes

### Phase 5: Ingestion parity

Goal:

- port chat parsing workflow

Tasks:

- regex extraction
- AI prompt rendering
- AI suggestion parsing
- regex amount override rule
- draft transaction creation
- parsed receipt persistence
- `POST /api/v1/ingestion/chat`

Done when:

- Go and Python ingestion behavior match for the main cases

### Phase 6: Reports parity

Goal:

- port daily/monthly reporting

Tasks:

- report repository
- daily auto-generation
- monthly first-day auto-generation
- manual monthly generation
- report prompt rendering
- deterministic fallback when AI unavailable

Done when:

- dashboard reports work fully against Python

### Phase 7: Review flow

Goal:

- implement the next missing product feature directly in Python

Tasks:

- parsed receipt listing
- review page APIs
- confirm/correct hooks
- draft review flow in frontend

Done when:

- `ReviewPage` becomes functional

### Phase 8: Cutover

Goal:

- switch development and CI to Python backend

Tasks:

- update frontend API target if needed
- add Python CI workflow
- keep Go backend only as fallback during short transition
- retire Go backend after confidence window

Done when:

- Python backend is the default backend

## Testing plan

Python test layers should mirror what currently exists in Go.

Required:

- domain tests for metrics, ingestion, reports, transactions
- API tests for route contracts
- infrastructure tests for Sheets bootstrap and repositories
- AI client tests with mocked HTTP

Parity checks:

- compare important payload shapes against current frontend expectations
- test regex amount override rule explicitly
- test daily/monthly report generation dates explicitly

## Recommended immediate next step

The very next implementation step after this document:

1. scaffold `backend_py/` with FastAPI, config, test setup, and health route
2. port config loading and the AI client layer first
3. then port transactions/goals/rules before metrics

Reason:

- config and infrastructure are the shared foundation
- metrics and ingestion depend on those layers
- it reduces rework during the migration

## Notes for future continuation

- keep the Go backend as a working reference until Python reaches parity
- do not delete Go yet
- prefer preserving API contract over “clean redesign” during migration
- once parity is reached, new product features should land in Python only
