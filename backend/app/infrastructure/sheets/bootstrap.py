from __future__ import annotations

from app.infrastructure.sheets.types import Bootstrapper, SheetSpec, SpreadsheetAdminAPI, ValuesAPI


def required_sheets() -> list[SheetSpec]:
    return [
        SheetSpec(
            title="Transactions",
            headers=[
                "Tx_ID",
                "Occurred_At",
                "Type",
                "Amount",
                "Currency",
                "Jar_Code",
                "Goal_Name",
                "Account_Name",
                "Is_Fixed",
                "Note",
                "Source",
                "Status",
                "Created_At",
                "Updated_At",
            ],
        ),
        SheetSpec(
            title="Goals",
            headers=["Goal_Name", "Target_Amount", "Start_Date", "Target_Date", "Status"],
        ),
        SheetSpec(
            title="NW_Snapshots",
            headers=["Month_Year", "Total_NW", "Liquid_NW", "Created_At"],
        ),
        SheetSpec(
            title="Fixed_Cost_Rules",
            headers=["Rule_Name", "Expected_Amount", "Window_Start_Day", "Window_End_Day", "Linked_Jar_Code", "Is_Active"],
        ),
        SheetSpec(
            title="Audit_Log",
            headers=["Audit_ID", "Tx_ID", "Action", "Previous_Value", "New_Value", "Reason", "Actor", "Created_At"],
        ),
        SheetSpec(
            title="Parsed_Receipts",
            headers=[
                "Receipt_ID",
                "Tx_ID",
                "Raw_Input",
                "Regex_Amount",
                "Regex_Tags",
                "LLM_Model",
                "LLM_Output_JSON",
                "Validation_Notes",
                "Confidence",
                "Prompt_Source",
                "Created_At",
            ],
        ),
        SheetSpec(
            title="Settings",
            headers=["Key", "Value", "Description"],
        ),
        SheetSpec(
            title="Reports",
            headers=[
                "Report_ID",
                "Kind",
                "Period_Key",
                "Title",
                "Summary",
                "Body",
                "Verdict",
                "Status",
                "Model",
                "Prompt_Source",
                "Trigger",
                "Created_At",
            ],
        ),
    ]


class SpreadsheetBootstrapper(Bootstrapper):
    def __init__(self, admin: SpreadsheetAdminAPI, values: ValuesAPI, spreadsheet_id: str) -> None:
        self._admin = admin
        self._values = values
        self._spreadsheet_id = spreadsheet_id

    def bootstrap(self) -> None:
        existing_titles = self._admin.get_sheet_titles(self._spreadsheet_id)
        missing_titles = [spec.title for spec in required_sheets() if spec.title not in existing_titles]
        self._admin.add_sheets(self._spreadsheet_id, missing_titles)

        for spec in required_sheets():
            rows = self._values.get(self._spreadsheet_id, f"{spec.title}!1:1")
            if headers_match(rows, spec.headers):
                continue
            self._values.update(self._spreadsheet_id, f"{spec.title}!A1", [spec.headers])


class NoopBootstrapper(Bootstrapper):
    def bootstrap(self) -> None:
        return None


def headers_match(rows: list[list[object]], expected: list[object]) -> bool:
    if not rows or len(rows[0]) < len(expected):
        return False

    return all(stringify(rows[0][index]) == stringify(value) for index, value in enumerate(expected))


def stringify(value: object) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    return str(value)
