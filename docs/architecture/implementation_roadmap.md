# Implementation Roadmap

## Goal

Turn the requirement docs into an implementation sequence that is:

- small enough to start fast,
- strict enough to stay maintainable,
- and structured enough for CI/CD from day one.

## Phase 0: Bootstrap the repository

Create this structure first:

```text
/
  frontend/
  backend/
  docs/
  infra/
  .github/workflows/
```

### Frontend bootstrap

- Vue 3 + Vite + TypeScript
- Vue Router
- Pinia
- TanStack Query
- Tailwind CSS
- Vitest
- Playwright
- ESLint
- Prettier

### Backend bootstrap

- Go module
- Fiber router
- Google Sheets client
- service interfaces
- test helpers
- linter config

### Infra bootstrap

- `.env.example`
- Makefile or Taskfile
- service account setup notes

## Phase 1: Build the non-AI core first

Do not start with chat or LLM. Build the ledger first.

### Backend

- Sheets repository layer
- `Transactions` APIs
- `Goals` APIs
- `Fixed_Cost_Rules` APIs
- `Settings` APIs

### Frontend

- app shell
- dashboard placeholder
- transactions list
- transaction create/edit form
- goals list
- settings for jars and thresholds

### Done when

- You can manually create income, expense, and transfer transactions.
- You can mark transactions as fixed or variable.
- You can create goals and fixed-cost rules.

## Phase 2: Implement metrics from stored data

Once ledger data exists, implement metrics without any LLM dependency.

### Backend services

- `sts_service`
- `anomaly_service`
- `pol_service`
- `tar_service`
- `goal_projection_service`

### Frontend widgets

- STS card
- daily spend chart
- fixed-cost status card
- goal progress card
- monthly report views

### Done when

- The dashboard works from manually entered data.
- All metric calculations are unit-tested.

## Phase 3: Add ingestion and human review

This is where AI enters the system.

### Backend

- chat webhook endpoint
- regex extractor
- prompt builder
- LLM parser adapter
- validation pipeline
- draft transaction creation
- correction and undo endpoints
- `Parsed_Receipts` writes
- `Audit_Log` writes

### Frontend

- review queue
- parsed transaction detail view
- one-click correction actions
- undo flow

### Done when

- A raw chat message becomes a reviewable transaction.
- Regex always wins for amount extraction.
- Every correction leaves an audit record.

## Phase 4: Add automation

### Jobs

- daily STS summary
- fixed-cost overdue scan
- monthly net worth snapshot
- monthly TAR summary

### Notifications

- chat notification templates
- in-app notification center

### Done when

- The system can operate proactively, not just reactively.

## Phase 5: Polish and reliability

### Add

- search and filters
- bulk edit
- CSV import/export
- dashboard cache sheet
- better dashboard visuals

## Initial folder design

## Frontend

```text
frontend/src/
  app/
  api/
  router/
  stores/
  features/
    dashboard/
    transactions/
    review/
    goals/
    metrics/
    settings/
  components/
  composables/
  lib/
  styles/
```

## Backend

```text
backend/
  cmd/api/
  internal/
    app/
    http/
    config/
    sheets/
    domain/
      transaction/
      metrics/
      goals/
      rules/
      ingestion/
      notifications/
    jobs/
    llm/
```

## Suggested MVP scope

If you want the fastest path to a usable product, define MVP as:

1. Manual transaction entry
2. Transaction list and filters
3. STS metric
4. Goal tracking
5. Chat parsing with correction flow

Delay these until later:

- multi-user support
- advanced portfolio valuation
- heavy notification logic
- large formula-based analytics sheets

## CI/CD checklist

### Every pull request

- frontend lint
- frontend type-check
- frontend unit test
- frontend build
- backend fmt check
- backend lint
- backend unit test
- API contract validation

### On merge to `main`

- build frontend artifact
- build backend artifact
- deploy backend
- deploy frontend

## Recommended coding standards

### Frontend

- smart pages, dumb reusable components
- API access only through `api/` layer
- no direct fetch calls inside random components
- keep forms close to their feature modules

### Backend

- handlers only orchestrate
- services own business logic
- Sheets gateway owns read/write details
- algorithms stay pure where possible

## Architecture decision summary

Use this sequence:

1. Build the Sheets-backed ledger
2. Build metrics in Go
3. Add AI ingestion
4. Add automation
5. Add polish

This keeps the project fast to implement while avoiding the fragility of putting too much production logic directly into spreadsheet formulas.
