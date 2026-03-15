# Grand Design

## 1. Purpose

This document is the implementation-ready system blueprint for the project.

It replaces the old split between:

- spreadsheet-driven calculations,
- mixed architecture notes,
- and isolated algorithm documents.

The legacy docs are preserved under `docs/legacy/requirements/` as business context and historical reference.

## 2. Product Definition

The product is a personal financial operating system with chat-first capture and web-first control.

Core outcomes:

- capture income, expenses, and transfers quickly,
- classify spending into jars and goals,
- let AI assist without becoming the source of truth,
- compute actionable financial metrics,
- give the user immediate correction power,
- and support reliable automation through code, tests, and CI/CD.

## 3. Guiding Principles

### Source of truth

- Google Sheets is the source of record for v1.
- Backend code owns domain logic and validation.
- AI helps interpret text only.
- Frontend renders and edits state, but does not own calculations.

### Reliability

- Every financial mutation is auditable.
- Corrections and undo never hard-delete history.
- Deterministic calculations must not depend on prompts.

### Simplicity

- Start single-user.
- Start with one chat channel.
- Use a modular monolith, not microservices.

## 4. Final Target Architecture

```text
Chat Provider / Manual UI / Import
            |
            v
      Ingestion Layer
  (regex + prompt + validation)
            |
            v
      Transaction Workflow
 (draft, review, correct, confirm)
            |
            v
       Google Sheets
            |
   ----------------------
   |                    |
   v                    v
Metrics Engine      Query API
   |                    |
   -----------  ---------
              v
         Vue Frontend
              |
              v
      Dashboard / Review / Goals
```

## 5. System Context

## Actors

- User via chat
- User via Vue web app
- Scheduled jobs
- Optional external services:
  - LLM provider
  - chat provider

## Main capabilities

- capture and review transactions
- manage jars and goals
- classify fixed vs variable spend
- compute STS, anomaly, POL, TAR, and goal ETA
- push proactive alerts
- maintain audit history

## 6. Technology Decisions

## Frontend

- Vue 3
- TypeScript
- Vite
- Vue Router
- Pinia
- TanStack Query
- Tailwind CSS
- Vitest
- Playwright

## Backend

- Go
- Fiber
- Google Sheets API
- OpenAPI
- background jobs inside the same codebase

Reason:

- low ops cost,
- simple hosting,
- easy manual inspection,
- good fit for a personal project with chat automation.

## Infrastructure

- frontend and backend deployed independently
- Google service account for Sheets access
- GitHub Actions for CI/CD
- no Redis in MVP
- no database server in MVP

## 7. Repository Layout

```text
/
  frontend/
  backend/
  docs/
    architecture/
    legacy/
    scripts/
  infra/
  .github/workflows/
```

## Frontend structure

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

## Backend structure

```text
backend/
  cmd/api/
  internal/
    app/
    config/
    sheets/
    http/
    domain/
      transactions/
      ingestion/
      metrics/
      goals/
      rules/
      accounts/
      notifications/
    jobs/
    llm/
    audit/
  testdata/
```

## 8. Google Sheets Design

Use separate sheets for raw records, configuration, and derived outputs.

### Raw sheets

- `Transactions`
- `Goals`
- `NW_Snapshots`
- `Fixed_Cost_Rules`
- `Audit_Log`
- `Parsed_Receipts`
- `Settings`

### Optional derived sheets

- `Metrics_Engine`
- `Dashboard_Cache`
- `Daily_Agg`
- `Monthly_Agg`

Rule:

- raw sheets are written by backend,
- derived sheets may be written by backend or use light formulas,
- critical business logic stays in Go.

## 9. Domain Modules

## 9.1 Ingestion

Input sources:

- chat webhook
- manual entry in web app
- future CSV import

Responsibilities:

- normalize raw input
- extract amount and tags via regex
- call LLM parser
- apply validation rules
- create draft transaction
- store parse metadata in `Parsed_Receipts`

## 9.2 Transaction Workflow

Responsibilities:

- create transaction drafts
- confirm or auto-confirm
- support correction
- support undo
- write audit entries

States:

- `draft`
- `confirmed`
- `reverted`

Represent these as status columns in Sheets.

## 9.3 Ledger

Responsibilities:

- store income, expense, and transfer records
- manage accounts, jars, goals
- support fixed-cost rules
- provide queryable historical data to the API

## 9.4 Metrics Engine

Owns the implementation of:

- STS
- bifurcated anomaly detection
- POL
- runway
- TAR
- goal velocity and ETA

Rule:

- metric code should be implemented in Go,
- formulas in Sheets should stay lightweight and non-critical.

## 9.5 Notification Engine

Responsibilities:

- daily briefing
- overdue fixed-cost alerts
- anomaly alerts
- monthly summary alerts
- goal milestone alerts

## 10. Sheet Schema

## `Transactions`

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

## `Parsed_Receipts`

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

## `Audit_Log`

- `Audit_ID`
- `Tx_ID`
- `Action`
- `Previous_Value`
- `New_Value`
- `Reason`
- `Actor`
- `Created_At`

## `Goals`

- `Goal_Name`
- `Target_Amount`
- `Start_Date`
- `Target_Date`
- `Status`

## `Fixed_Cost_Rules`

- `Rule_Name`
- `Expected_Amount`
- `Window_Start_Day`
- `Window_End_Day`
- `Linked_Jar_Code`
- `Is_Active`

## `NW_Snapshots`

- `Month_Year`
- `Total_NW`
- `Liquid_NW`
- `Created_At`

## `Settings`

- `Key`
- `Value`
- `Description`

## 11. Canonical Flows

## 11.1 Chat-to-transaction flow

1. User sends a chat message.
2. Backend webhook receives raw text.
3. Regex extracts amount and tags.
4. LLM returns structured interpretation.
5. Validation applies hard rules.
6. Transaction row is created in `Transactions`.
7. Parse metadata is written to `Parsed_Receipts`.
8. Bot returns receipt with correction shortcuts.
9. User may correct or undo.
10. Backend updates the row and appends `Audit_Log`.

## 11.2 Manual web transaction flow

1. User opens transaction form in Vue.
2. Client validates shape.
3. Backend validates business rules.
4. Backend appends or updates row in `Transactions`.
5. Dashboard cache and metrics are refreshed.

## 11.3 Monthly close flow

1. Read current balances and accounts.
2. Write month snapshot to `NW_Snapshots`.
3. Calculate TAR in backend.
4. Refresh summary outputs.
5. Send monthly summary.

## 12. Hard Validation Rules

- Regex amount overrides LLM amount when mismatch exists.
- Only allowed jar codes may be stored.
- `TRANSFER` must target a jar or goal.
- `OUT` with `is_fixed = true` should be checked against fixed-cost rules.
- `reverted` transactions remain in history.
- All corrections append `Audit_Log`.
- Financial calculations only use valid non-reverted records.

## 13. Metrics Definitions

## STS

Purpose:

- produce a daily safe-to-spend number for variable expenses.

Inputs:

- monthly variable budget
- variable spend to date
- days remaining

Output:

- current amount
- yesterday delta
- status level

## Bifurcated anomaly detection

Purpose:

- separate fixed-cost behavior from variable spend anomalies.

Outputs:

- fixed-cost overdue statuses
- variable-spend z-score
- anomaly level

## POL + runway

Purpose:

- measure structural risk.

Outputs:

- fixed-cost ratio
- runway months
- quadrant classification

## TAR

Purpose:

- compare net worth growth against income.

Outputs:

- NSR
- TAR
- spread between TAR and NSR

## Goal velocity + ETA

Purpose:

- measure actual saving speed and completion estimate.

Outputs:

- progress
- 3-month average velocity
- ETA
- scenario simulation inputs

## 14. API Surface

## Ingestion and transactions

- `POST /api/v1/ingestion/chat`
- `POST /api/v1/transactions`
- `GET /api/v1/transactions`
- `GET /api/v1/transactions/:id`
- `PATCH /api/v1/transactions/:id`
- `POST /api/v1/transactions/:id/correct`
- `POST /api/v1/transactions/:id/undo`

## Dashboard and metrics

- `GET /api/v1/dashboard/summary`
- `GET /api/v1/metrics/sts`
- `GET /api/v1/metrics/anomalies`
- `GET /api/v1/metrics/pol`
- `GET /api/v1/metrics/tar`

## Goals and rules

- `GET /api/v1/goals`
- `POST /api/v1/goals`
- `GET /api/v1/goals/:id/projection`
- `GET /api/v1/fixed-cost-rules`
- `POST /api/v1/fixed-cost-rules`

## 15. Frontend Screens

## Dashboard

Shows:

- current STS
- anomaly state
- POL and runway summary
- TAR summary
- top goals
- recent transactions

## Transactions

Shows:

- transaction list
- filters
- create and edit form
- fixed vs variable split

## Review Queue

Shows:

- AI-parsed transactions needing review
- quick correction choices
- undo actions
- parser metadata for debugging

## Goals

Shows:

- progress cards
- ETA
- velocity
- future simulation slider

## Settings

Shows:

- jar configuration
- budgets
- thresholds
- fixed-cost rules
- accounts and snapshot settings

## 16. Jobs and Automation

## Daily jobs

- recalculate STS
- scan fixed-cost overdue windows
- compute dashboard summaries
- send briefing if enabled

## Monthly jobs

- take net worth snapshot
- calculate TAR
- roll monthly summaries
- send monthly report

## 17. CI/CD Design

## Pull request CI

- frontend lint
- frontend type-check
- frontend unit tests
- frontend build
- backend format check
- backend lint
- backend unit tests
- API contract validation

## Deploy flow

- merge to `main`
- build frontend artifact
- build backend artifact
- deploy backend
- deploy frontend

## Required quality gates

- protected `main`
- versioned API changes
- no production-critical logic hidden only in formulas

## 18. Delivery Plan

## Phase 1

- scaffold repo
- setup Vue app
- setup Go API
- setup Google Sheets client
- setup CI/CD

## Phase 2

- manual ledger CRUD
- jars
- goals
- fixed-cost rules

## Phase 3

- metrics engine
- dashboard widgets
- reports

## Phase 4

- chat ingestion
- LLM parsing
- review workflow
- undo and correction

## Phase 5

- daily jobs
- monthly jobs
- notifications
- export and polish

## 19. Non-Goals for MVP

- multi-user teams
- complex gamification engine
- task management subsystem
- PostgreSQL migration in v1
- microservice split

These can be reconsidered later after the finance core is stable.

## 20. Decision Summary

This system should be built as:

- `Vue 3 + TypeScript` frontend
- `Go + Fiber` backend
- `Google Sheets` as v1 source of record
- `LLM-assisted ingestion with human correction`
- `code-based metrics engine`
- `CI/CD from day one`

That is the cleanest path from the old requirement docs to a system that is realistic to implement quickly for a personal project without introducing unnecessary infrastructure.
