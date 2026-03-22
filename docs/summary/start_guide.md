# Start Guide

This guide gets the project running locally in two modes:

- memory mode, with no real Google services
- real mode, with Google Sheets and Google AI API

## 1. Install dependencies

Backend:

```bash
cd backend
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
```

Frontend:

```bash
cd frontend
npm install
```

## 2. Create local config

Create or edit `config/local.yaml`.

This file is gitignored and intended for local or server-specific secrets.

Use this as a starting point:

```yaml
app:
  env: development
  port: "8080"
  timezone: Asia/Ho_Chi_Minh

sheets:
  spreadsheet_id: ""
  service_account_file: /app/config/metrickey.json

ai:
  provider: gemini
  base_url: https://generativelanguage.googleapis.com
  api_key: "REPLACE_WITH_GOOGLE_AI_API_KEY"
  model: gemma-3-27b-it
  prompt_file: ./prompts/chat_parser.default.txt
  daily_report_prompt_file: ./prompts/daily_report.default.txt
  monthly_report_prompt_file: ./prompts/monthly_report.default.txt
```

Notes:

- Leave `sheets.spreadsheet_id` empty if you want memory mode.
- Prompt editing should happen in the `.txt` files under `prompts/`.
- Most parsing input is expected to come from Google Chat style messages.
- Service account should be provided from `config/metrickey.json`.
- API key should be provided in `config/local.yaml`.

## 3. Fastest real run

Fill these values in `config/local.yaml`:

- `sheets.spreadsheet_id`
- `sheets.service_account_file`
- `ai.api_key`

Also place your Google service account JSON at:

- `config/metrickey.json`

Then run:

```bash
docker compose up --build
```

That is enough for a basic real run.

If you only want memory mode for now:

- keep `sheets.spreadsheet_id` empty
- `service_account_file` and `ai.api_key` can stay as placeholders

## 4. Run backend

From the repo root:

```bash
make run-backend
```

Backend API will run at:

- `http://0.0.0.0:8080`

Notes:

- `make run-backend` now uses `config/local.yaml` by default
- it resolves the config path from the repo root, so it is safer than relying on a relative path after `cd backend`
- for local-only binding, use:

```bash
make run-backend-local
```

Production-style local run with Docker:

```bash
docker compose up --build
```

This starts:

- backend on `http://127.0.0.1:8080`
- frontend on `http://127.0.0.1:3000`

Health check:

```bash
curl http://127.0.0.1:8080/api/v1/health
```

Expected result:

```json
{"status":"ok"}
```

## 5. Run frontend

In another terminal:

```bash
cd frontend
VITE_API_BASE_URL=http://127.0.0.1:8080 npm run dev
```

Then open the Vite URL shown in the terminal.

## 6. Memory mode smoke test

This works without real Google config.

Try this order:

1. Open `Transactions` and create a manual transaction.
2. Open `Dashboard` and confirm metrics and reports render.
3. Call the ingestion API with a Google Chat style message.
4. Open `Review` and confirm, correct, or revert the draft.

Example ingestion request:

```bash
curl -X POST http://127.0.0.1:8080/api/v1/ingestion/chat \
  -H "Content-Type: application/json" \
  -d '{
    "rawInput":"an trua voi team 150k #food",
    "source":"google-chat"
  }'
```

## 7. Real Google Sheets mode

When you are ready for real persistence:

1. Create a Google Sheet.
2. Put its ID into `sheets.spreadsheet_id`.
3. Share the sheet with the service account email inside `config/metrickey.json`.
4. Start the backend.
5. Call:

```bash
curl -X POST http://127.0.0.1:8080/api/v1/admin/bootstrap
```

This prepares the required tabs and headers.

Then repeat the smoke test and confirm rows are written into:

- `Transactions`
- `Parsed_Receipts`
- `Reports`
- `Audit_Log`

## 8. Real Google AI mode

When `ai.provider` is `gemini` and `ai.api_key` is filled, the backend will use:

- Google AI API
- model `gemma-3-27b-it`

Use real Google Chat-like messages during testing so you can tune:

- `prompts/chat_parser.default.txt`
- `prompts/daily_report.default.txt`
- `prompts/monthly_report.default.txt`

The response parser extracts JSON from model output with regex before parsing. The model can include extra prose around the JSON block, but cleaner prompt output is still better.

## 9. Google Chat integration

Backend webhook route:

- `POST /api/v1/integrations/google-chat/events`

Recommended Google Chat app setup:

1. Create a Google Chat app in Google Cloud / Google Chat configuration.
2. Configure it as an HTTP app.
3. Point the app URL to:

```text
https://YOUR_PUBLIC_BASE_URL/api/v1/integrations/google-chat/events
```

For local Docker, this route exists at:

```text
http://127.0.0.1:8080/api/v1/integrations/google-chat/events
```

Supported event behavior:

- `ADDED_TO_SPACE`: returns a short intro message
- `MESSAGE`: parses the message and creates a draft transaction
- slash-command style messages use `message.argumentText` when present

Recommended Chat usage:

- direct message the bot with text like `an trua 150k #food`
- or use a slash command like `/log an trua 150k #food`
- then open the `Review` page to confirm or correct the draft

## 10. Test commands

Backend:

```bash
backend/.venv/bin/python -m pytest
```

Frontend tests:

```bash
cd frontend
npm test
```

Frontend production build:

```bash
cd frontend
npm run build
```

Docker image builds:

```bash
docker build -f backend/Dockerfile .
docker build -f frontend/Dockerfile .
```

## 11. If something fails

Quick checks:

- confirm `config/local.yaml` exists
- confirm backend is running on port `8080`
- confirm frontend uses `VITE_API_BASE_URL=http://127.0.0.1:8080`
- confirm prompt files exist under `prompts/`
- confirm the sheet is shared with the service account email
- confirm `config/metrickey.json` exists and contains a valid Google service account JSON
- confirm `ai.api_key` is a real Google AI API key
- confirm your Google Chat app points to `/api/v1/integrations/google-chat/events`

## 12. Secret safety

Local secret paths are already ignored from git:

- `config/local.yaml`
- `config/*.local.yaml`
- `secrets/`
- `.dockerignore` also excludes them from Docker build context

Recommended habit:

- keep real spreadsheet IDs and API keys only in `config/local.yaml`
- keep the real Google service account JSON only in `config/metrickey.json`
- do not place real keys in `config/app.example.yaml`
- do not place real prompt content in YAML when prompt files are already used

## 13. Recommended first real run

Best first real run order:

1. Start in memory mode.
2. Test manual transactions and review flow.
3. Enable Google Sheets and bootstrap the spreadsheet.
4. Enable Google AI API with `gemma-3-27b-it`.
5. Tune prompts using real Google Chat messages.
