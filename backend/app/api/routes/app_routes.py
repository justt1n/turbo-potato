from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.core.dependencies import (
    get_assets_service,
    get_bootstrapper,
    get_jars_service,
    get_goals_service,
    get_google_chat_service,
    get_ingestion_service,
    get_legacy_jar_migration_service,
    get_metrics_service,
    get_parsed_receipt_review_service,
    get_reports_service,
    get_rules_service,
    get_sources_service,
    get_transaction_service,
)
from app.domain.jars.model import CreateInput as CreateJarInput
from app.domain.jars.model import UpdateInput as UpdateJarInput
from app.domain.goals.model import CreateInput as CreateGoalInput
from app.domain.goals.model import UpdateInput as UpdateGoalInput
from app.domain.ingestion.model import IngestInput, ReviewActionInput, ReviewCorrectInput
from app.domain.migrations.model import MigrateLegacyJarsInput
from app.domain.reports.model import GenerateInput
from app.domain.rules.model import CreateFixedCostRuleInput
from app.domain.rules.model import UpdateFixedCostRuleInput
from app.domain.sources.model import CreateInput as CreateSourceInput
from app.domain.sources.model import UpdateInput as UpdateSourceInput
from app.domain.transactions.model import CreateInput, UpdateInput

router = APIRouter()


@router.post("/admin/bootstrap")
def bootstrap() -> dict[str, str]:
    get_bootstrapper().bootstrap()
    return {"status": "bootstrapped"}


@router.post("/admin/initialize-system")
def initialize_system():
    get_bootstrapper().bootstrap()
    seeded = get_jars_service().seed_default_jars()
    return {
        "status": "initialized",
        "bootstrapStatus": "bootstrapped",
        "defaultJars": {
            "created": seeded.created,
            "skipped": seeded.skipped,
            "items": seeded.items,
        },
    }


@router.post("/admin/seed-default-jars")
def seed_default_jars():
    get_bootstrapper().bootstrap()
    result = get_jars_service().seed_default_jars()
    return {
        "created": result.created,
        "skipped": result.skipped,
        "items": result.items,
    }


@router.post("/admin/migrate-legacy-jars")
def migrate_legacy_jars(request: MigrateLegacyJarsInput):
    get_bootstrapper().bootstrap()
    return get_legacy_jar_migration_service().migrate_legacy_jars(request.dry_run).model_dump(by_alias=True)


@router.get("/dashboard/summary")
def dashboard_summary():
    return get_metrics_service().summary().model_dump(by_alias=True)


@router.get("/dashboard/reports")
def dashboard_reports():
    return get_reports_service().dashboard().model_dump(by_alias=True, exclude_none=True)


@router.post("/dashboard/reports/monthly", status_code=201)
def generate_monthly_report(request: GenerateInput):
    return get_reports_service().generate_monthly(request).model_dump(by_alias=True)


@router.get("/transactions")
def list_transactions():
    items = [item.model_dump(by_alias=True) for item in get_transaction_service().list()]
    return {"items": items}


@router.post("/transactions", status_code=201)
def create_transaction(request: CreateInput):
    try:
        return get_transaction_service().create(request).model_dump(by_alias=True)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/transactions/{tx_id}/correct")
def correct_transaction(tx_id: str, request: dict):
    try:
        update = UpdateInput.model_validate(request)
        result = get_transaction_service().correct(tx_id, update, str(request.get("reason", "")), str(request.get("actor", "")))
        return result.model_dump(by_alias=True)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/transactions/{tx_id}/undo")
def undo_transaction(tx_id: str, request: dict):
    try:
        return get_transaction_service().undo(tx_id, str(request.get("reason", "")), str(request.get("actor", ""))).model_dump(by_alias=True)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/goals")
def list_goals():
    return {"items": [item.model_dump(by_alias=True) for item in get_goals_service().list()]}


@router.post("/goals", status_code=201)
def create_goal(request: CreateGoalInput):
    try:
        return get_goals_service().create(request).model_dump(by_alias=True)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/goals/{goal_name}")
def update_goal(goal_name: str, request: UpdateGoalInput):
    try:
        return get_goals_service().update(goal_name, request).model_dump(by_alias=True)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/jars")
def list_jars():
    return {"items": [item.model_dump(by_alias=True) for item in get_jars_service().list()]}


@router.post("/jars", status_code=201)
def create_jar(request: CreateJarInput):
    try:
        return get_jars_service().create(request).model_dump(by_alias=True)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/jars/{jar_code}")
def update_jar(jar_code: str, request: UpdateJarInput):
    try:
        return get_jars_service().update(jar_code, request).model_dump(by_alias=True)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/assets/overview")
def assets_overview():
    return get_assets_service().overview().model_dump(by_alias=True)


@router.get("/sources")
def list_sources():
    return {"items": [item.model_dump(by_alias=True) for item in get_sources_service().list()]}


@router.post("/sources", status_code=201)
def create_source(request: CreateSourceInput):
    try:
        return get_sources_service().create(request).model_dump(by_alias=True)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/sources/{source_code}")
def update_source(source_code: str, request: UpdateSourceInput):
    try:
        return get_sources_service().update(source_code, request).model_dump(by_alias=True)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/fixed-cost-rules")
def list_fixed_cost_rules():
    return {"items": [item.model_dump(by_alias=True) for item in get_rules_service().list_fixed_cost_rules()]}


@router.post("/fixed-cost-rules", status_code=201)
def create_fixed_cost_rule(request: CreateFixedCostRuleInput):
    try:
        return get_rules_service().create_fixed_cost_rule(request).model_dump(by_alias=True)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/fixed-cost-rules/{rule_name}")
def update_fixed_cost_rule(rule_name: str, request: UpdateFixedCostRuleInput):
    try:
        return get_rules_service().update_fixed_cost_rule(rule_name, request).model_dump(by_alias=True)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/ingestion/chat", status_code=201)
def ingest_chat(request: IngestInput):
    try:
        return get_ingestion_service().ingest_chat(request).model_dump(by_alias=True)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/integrations/google-chat/events")
def google_chat_event(request: dict):
    try:
        return get_google_chat_service().handle_event(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/parsed-receipts")
def list_parsed_receipts():
    items = [item.model_dump(by_alias=True, exclude_none=True) for item in get_parsed_receipt_review_service().list()]
    return {"items": items}


@router.get("/parsed-receipts/{receipt_id}")
def get_parsed_receipt(receipt_id: str):
    try:
        return get_parsed_receipt_review_service().get(receipt_id).model_dump(by_alias=True, exclude_none=True)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/parsed-receipts/{receipt_id}/confirm")
def confirm_parsed_receipt(receipt_id: str, request: ReviewActionInput):
    try:
        return get_parsed_receipt_review_service().confirm(receipt_id, request.reason, request.actor).model_dump(by_alias=True, exclude_none=True)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/parsed-receipts/{receipt_id}/correct")
def correct_parsed_receipt(receipt_id: str, request: ReviewCorrectInput):
    try:
        return get_parsed_receipt_review_service().correct(receipt_id, request).model_dump(by_alias=True, exclude_none=True)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/parsed-receipts/{receipt_id}/undo")
def undo_parsed_receipt(receipt_id: str, request: ReviewActionInput):
    try:
        return get_parsed_receipt_review_service().undo(receipt_id, request.reason, request.actor).model_dump(by_alias=True, exclude_none=True)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
