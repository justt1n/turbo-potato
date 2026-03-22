# User Guide

This guide explains how to use Turbo Potato after the app is already running.

If you still need setup steps, use [start_guide.md](/Users/admin/code/turbo-potato/docs/summary/start_guide.md).

## What the app does

Turbo Potato is a personal finance workflow with four main ideas:

- capture transactions quickly
- let AI draft a transaction from chat-style text
- review and correct drafts before final confirmation
- monitor financial health from the dashboard

The system is designed around Google Chat-style input and Google Sheets storage.

## Main navigation

The app has these main screens:

- `Dashboard`
- `Transactions`
- `Review`
- `Goals`
- `Settings`

Right now, the most important screens are `Dashboard`, `Transactions`, and `Review`.

## Daily workflow

Recommended daily flow:

1. Log spending or income from Google Chat, or enter it manually in `Transactions`.
2. Open `Review`.
3. Confirm or correct AI-created drafts.
4. Check `Dashboard` for daily posture and reports.

## Logging from Google Chat

The most common input is expected to come from Google Chat.

Examples:

```text
an trua 150k #food
```

```text
thu freelance 2tr #sidehustle
```

```text
/log mua sach 320k #study
```

What happens:

1. Google Chat sends the message to the backend webhook.
2. The backend extracts the transaction meaning.
3. A draft transaction is created.
4. The draft appears in the `Review` screen.

Important:

- Chat messages are not treated as final confirmed transactions
- they go through review first

## Entering a transaction manually

Use the `Transactions` page when you want full manual control.

Fields:

- `Type`: `Expense`, `Income`, or `Transfer`
- `Amount`
- `Jar code`
- `Goal name`
- `Account`
- `Note`
- `Fixed cost`

Use manual entry when:

- the AI parser got confused
- you want to log something carefully
- you are backfilling older records

## Reviewing AI drafts

The `Review` page is the human-in-the-loop control point.

Each card shows:

- original raw input
- regex amount
- linked draft transaction
- status
- prompt source
- model output payload

Available actions:

- `Confirm draft`
- `Correct draft`
- `Revert draft`

### Confirm draft

Use this when the draft already looks correct.

Result:

- transaction status becomes `confirmed`

### Correct draft

Use this when the AI draft is close but not perfect.

You can edit:

- type
- amount
- jar code
- goal name
- account
- note
- fixed-cost flag
- reason

Result:

- the draft is updated
- the corrected transaction is saved as `confirmed`

### Revert draft

Use this when the draft should not count.

Result:

- transaction status becomes `reverted`
- the item stays in history but is treated as cancelled

## Understanding the dashboard

The `Dashboard` gives a quick finance snapshot.

Main sections:

- ring metrics
- baseline monitor
- operating posture
- daily report
- monthly report

### Ring metrics

These summarize:

- spending pressure
- anomaly level
- goal pace

They are backend-driven, so the frontend is only displaying what the backend calculates.

### Baseline monitor

This tracks multiple baseline lines at once.

Typical baselines include:

- variable spend
- fixed-cost load
- goal velocity

### Operating posture

This is the top-level finance status summary.

Typical statuses:

- `healthy`
- `watch`
- `critical`

Use it as a quick “am I okay?” signal, not as accounting truth by itself.

### Daily report

The daily report is generated automatically.

It is meant to answer:

- what happened today
- whether spending pressure is okay
- whether something unusual happened

### Monthly report

The monthly report can be:

- generated manually from the dashboard
- auto-generated on the first day of the month

It is meant to answer:

- is the overall monthly financial state good
- what structural strengths exist
- what risks need attention

## Google Sheets behavior

Google Sheets is the v1 source of record.

Main tabs created by bootstrap include:

- `Transactions`
- `Goals`
- `NW_Snapshots`
- `Fixed_Cost_Rules`
- `Audit_Log`
- `Parsed_Receipts`
- `Settings`
- `Reports`

What gets written where:

- manual and confirmed transactions go to `Transactions`
- AI parse artifacts go to `Parsed_Receipts`
- corrections and undo actions go to `Audit_Log`
- reports go to `Reports`

## How to know the app is working

Good signs:

- `Dashboard` loads without error
- manual transactions appear in `Transactions`
- Chat-style input creates drafts in `Review`
- confirming a draft changes its status from `draft` to `confirmed`
- monthly report generation returns a new report
- rows appear in the expected Google Sheet tabs

## Common usage examples

Expense:

```text
an toi voi gia dinh 420k #food
```

Income:

```text
thu freelance 5tr #work
```

Transfer to a goal:

```text
chuyen 2tr vao quy mua xe
```

Fixed cost:

```text
tien nha 7tr
```

## What to do when something looks wrong

If a draft is wrong:

- open `Review`
- use `Correct draft`
- save the correction

If a draft should be ignored:

- use `Revert draft`

If the dashboard looks empty:

- check whether any confirmed transactions exist
- check whether the backend can reach Google Sheets
- check whether the sheet was bootstrapped

If reports sound strange:

- update the prompt files in `prompts/`
- test with real Google Chat examples

## Current limitations

The app is usable, but still not fully hardened.

Current limitations:

- Google Chat request verification is not implemented yet
- `Goals` and `Settings` are less complete than `Dashboard`, `Transactions`, and `Review`
- prompt tuning may still be needed for your real Google Chat message style
- production auth/security is not finished

## Recommended habit

Best ongoing habit:

1. capture quickly in Google Chat
2. review drafts in the app
3. confirm only what is correct
4. use the dashboard for trends, not raw bookkeeping alone
