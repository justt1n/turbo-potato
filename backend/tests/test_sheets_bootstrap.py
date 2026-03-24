from __future__ import annotations

from app.infrastructure.sheets.bootstrap import SpreadsheetBootstrapper, required_sheets


class FakeValuesClient:
    def __init__(self, rows: dict[str, list[list[object]]] | None = None) -> None:
        self.rows = rows or {}
        self.updated: dict[str, list[list[object]]] = {}

    def append(self, spreadsheet_id: str, read_range: str, values: list[list[object]]) -> None:
        raise AssertionError("append should not be used during bootstrap tests")

    def get(self, spreadsheet_id: str, read_range: str) -> list[list[object]]:
        return self.rows.get(read_range, [])

    def update(self, spreadsheet_id: str, read_range: str, values: list[list[object]]) -> None:
        self.updated[read_range] = values


class FakeAdminClient:
    def __init__(self, titles: list[str]) -> None:
        self.titles = list(titles)
        self.added: list[str] = []

    def get_sheet_titles(self, spreadsheet_id: str) -> list[str]:
        return list(self.titles)

    def add_sheets(self, spreadsheet_id: str, titles: list[str]) -> None:
        self.added.extend(titles)


def test_bootstrap_adds_missing_sheets() -> None:
    admin = FakeAdminClient(["Transactions"])
    values = FakeValuesClient()
    bootstrapper = SpreadsheetBootstrapper(admin, values, "sheet-id")

    bootstrapper.bootstrap()

    assert "Goals" in admin.added
    assert "Reports" in admin.added


def test_bootstrap_does_not_add_when_all_exist() -> None:
    admin = FakeAdminClient([spec.title for spec in required_sheets()])
    values = FakeValuesClient()
    bootstrapper = SpreadsheetBootstrapper(admin, values, "sheet-id")

    bootstrapper.bootstrap()

    assert admin.added == []


def test_bootstrap_writes_headers_when_missing() -> None:
    admin = FakeAdminClient([spec.title for spec in required_sheets()])
    values = FakeValuesClient()
    bootstrapper = SpreadsheetBootstrapper(admin, values, "sheet-id")

    bootstrapper.bootstrap()

    assert values.updated["Transactions!A1"][0][0] == "Tx_ID"
    assert values.updated["Reports!A1"][0][0] == "Report_ID"


def test_bootstrap_rewrites_mismatched_headers() -> None:
    admin = FakeAdminClient([spec.title for spec in required_sheets()])
    values = FakeValuesClient(rows={"Goals!1:1": [["Wrong_Header"]]})
    bootstrapper = SpreadsheetBootstrapper(admin, values, "sheet-id")

    bootstrapper.bootstrap()

    assert values.updated["Goals!A1"] == [["Goal_Name", "Target_Amount", "Start_Date", "Target_Date", "Status"]]


def test_bootstrap_skips_matching_headers() -> None:
    goals_headers = ["Goal_Name", "Target_Amount", "Start_Date", "Target_Date", "Status"]
    reports_headers = [
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
    ]
    admin = FakeAdminClient([spec.title for spec in required_sheets()])
    values = FakeValuesClient(
        rows={
            "Goals!1:1": [goals_headers],
            "Reports!1:1": [reports_headers],
        }
    )
    bootstrapper = SpreadsheetBootstrapper(admin, values, "sheet-id")

    bootstrapper.bootstrap()

    assert "Goals!A1" not in values.updated
    assert "Reports!A1" not in values.updated


def test_required_sheets_include_reports_and_parsed_receipts_headers() -> None:
    specs = {spec.title: spec.headers for spec in required_sheets()}

    assert specs["Parsed_Receipts"] == [
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
    ]
    assert specs["Reports"] == [
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
    ]
    assert specs["Sources"] == [
        "Source_Code",
        "Source_Name",
        "Kind",
        "Provider",
        "Linked_Jar_Code",
        "Opening_Balance",
        "Actual_Balance",
        "Gold_Quantity_Chi",
        "Gold_Price_Per_Chi",
        "Is_Active",
        "Note",
    ]
