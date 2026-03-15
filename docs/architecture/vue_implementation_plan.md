# Vue Implementation Plan

## 1. Product Direction

This project should be implemented as a small financial operating system with 3 clear layers:

1. `Frontend (Vue)` for dashboard, transaction review, goal planning, and settings.
2. `Backend API (Go)` for parsing, validation, transaction workflows, algorithm execution, and automation.
3. `Google Sheets` as the v1 source of record.

The current docs are strong on business rules. For v1, Google Sheets is acceptable and practical, but the backend should still own the critical logic instead of pushing everything into formulas.

## 2. Recommended Architecture Changes

### Keep

- Chat-first transaction capture.
- Regex + LLM hybrid parser.
- Human-in-the-loop correction flow.
- STS, anomaly detection, POL, TAR, and Goal ETA as first-class metrics.

### Change

- Replace `Google Sheets as full calculation engine` with `Google Sheets as storage + Go domain services for critical logic`.
- Keep formulas for light aggregation and visibility only.
- Keep the frontend as Vue 3 + TypeScript.

### Why this change is worth it

- Business logic stays testable.
- Frontend gets stable APIs instead of fragile cell dependencies.
- Correction and undo flows remain safe.
- You still keep the speed and simplicity of Google Sheets.

## 3. Target Tech Stack

### Frontend

- Vue 3
- TypeScript
- Vite
- Vue Router
- Pinia
- TanStack Query for Vue
- VueUse
- Tailwind CSS or UnoCSS
- `zod` for runtime schema validation at API boundaries
- ECharts or ApexCharts for metric visualizations

### Backend

- Go
- Fiber
- Google Sheets API
- OpenAPI for API contract generation
- Structured logging
- Background jobs inside the same service

### Infrastructure

- Google Sheets
- GitHub Actions for CI/CD
- Deploy frontend to Vercel or Cloudflare Pages
- Deploy backend to Fly.io, Railway, Render, or OCI free VM

## 4. System Modules

### 4.1 Ingestion Module

Responsibilities:

- receive raw messages
- extract amount and tags with regex
- call LLM parser
- run validation rules
- create transaction rows
- store parse metadata

### 4.2 Validation Module

Responsible for the soft-commit workflow from the legacy docs.

Responsibilities:

- save parsed result immediately
- allow one-click correction and undo
- maintain immutable audit trail

### 4.3 Ledger Module

Responsibilities:

- store transactions in Sheets
- store transfers between jars and goals
- store monthly snapshots
- expose query APIs to dashboard and bot

### 4.4 Metrics Module

Responsible for:

- Dynamic STS
- Bifurcated anomaly detection
- POL + runway matrix
- TAR
- Goal velocity + ETA

Rules:

- Each metric should live in isolated Go service code.
- Each metric should return both raw numbers and human-readable status levels.
- No frontend formula duplication.

## 5. Sheet Design Proposal

### Raw sheets

- `Transactions`
- `Goals`
- `NW_Snapshots`
- `Fixed_Cost_Rules`
- `Parsed_Receipts`
- `Audit_Log`
- `Settings`

### Derived sheets

- `Metrics_Engine`
- `Dashboard_Cache`
- `Daily_Agg`
- `Monthly_Agg`

### Important rule

Critical business logic should be in backend code, not only in formulas.

## 6. Data Shape Proposal

### `Transactions`

- `Tx_ID`
- `Occurred_At`
- `Type`
- `Amount`
- `Currency`
- `Jar_Code`
- `Goal_Name`
- `Account_Name`
- `Is_Fixed`
- `Note`
- `Source`
- `Status`
- `Created_At`
- `Updated_At`

### `Parsed_Receipts`

- `Receipt_ID`
- `Tx_ID`
- `Raw_Input`
- `Regex_Amount`
- `Regex_Tags`
- `LLM_Model`
- `LLM_Output_JSON`
- `Validation_Notes`
- `Confidence`
- `Created_At`

### `Audit_Log`

- `Audit_ID`
- `Tx_ID`
- `Action`
- `Previous_Value`
- `New_Value`
- `Reason`
- `Actor`
- `Created_At`

## 7. Frontend Architecture

### Pages

- `DashboardPage`
- `TransactionsPage`
- `TransactionReviewPage`
- `GoalsPage`
- `ReportsPage`
- `SettingsPage`

### Suggested feature-based structure

```text
frontend/
  src/
    app/
    router/
    stores/
    api/
    features/
      dashboard/
      transactions/
      review/
      goals/
      reports/
      settings/
    components/
    composables/
    utils/
    styles/
```

### UI priorities

- fast add/edit transaction flow
- clear distinction between fixed and variable spend
- review queue for AI-parsed items
- visual explanation for each metric
- goal simulator slider for ETA scenarios

## 8. API Design

### Main endpoints

- `POST /api/v1/ingestion/chat`
- `POST /api/v1/transactions`
- `GET /api/v1/transactions`
- `PATCH /api/v1/transactions/:id`
- `POST /api/v1/transactions/:id/undo`
- `POST /api/v1/transactions/:id/correct`
- `GET /api/v1/dashboard/summary`
- `GET /api/v1/metrics/sts`
- `GET /api/v1/metrics/anomalies`
- `GET /api/v1/metrics/pol`
- `GET /api/v1/metrics/tar`
- `GET /api/v1/goals`
- `GET /api/v1/goals/:id/projection`

### API response principle

Return both raw values and interpretation metadata.

## 9. Algorithm Execution Strategy

### Real-time

- regex parse
- LLM parse
- validation
- soft-commit
- recompute dashboard summary

### Scheduled

- daily STS refresh at local 07:00
- fixed-cost overdue scan daily
- monthly net worth snapshot on last day of month
- monthly TAR report on day 1

### Important rule

Prompting should help interpret raw messages, never own the financial truth.

## 10. CI/CD Initialization

## Repository shape

```text
/
  frontend/
  backend/
  docs/
  infra/
  .github/workflows/
```

## Minimum pipelines

### `ci-frontend.yml`

- install dependencies
- type-check
- lint
- unit tests
- build

### `ci-backend.yml`

- setup Go
- verify formatting
- run lints
- run unit tests
- verify Sheets integration interfaces

### `ci-contract.yml`

- validate OpenAPI schema
- verify no client/server contract drift

## 11. Recommended Delivery Phases

### Phase 1: Foundation

- create monorepo structure
- setup Vue app and Go service
- setup Google Sheets client
- add linting, tests, and GitHub Actions

### Phase 2: Transaction core

- manual transaction CRUD
- jar configuration
- fixed vs variable classification
- transaction list and filters

### Phase 3: Chat parsing

- chat webhook
- regex parser
- LLM parser
- validation pipeline
- soft-commit receipt flow

### Phase 4: Metrics dashboard

- STS
- anomaly detection
- POL + runway
- goal velocity + ETA
- TAR monthly report

### Phase 5: Automation and polish

- daily and monthly jobs
- notifications
- better charts
- performance tuning

## 12. Final Recommendation

Build `Google Sheets + Go API + Vue 3` as the main architecture for v1.

Use Sheets as the storage system, but keep validation, metrics, and workflow logic in Go so the project stays clean, readable, and maintainable.
