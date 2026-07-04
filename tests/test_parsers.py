from h1b_mcp.parsers.summary import summarize_h1bgrader_profile
from h1b_mcp.parsers.tables import parse_h1bgrader_profile
from tests.fixtures import DATABRICKS_PROFILE_HTML, DATABRICKS_PROFILE_TEXT, DATABRICKS_PROFILE_URL


def test_summarize_profile_classifies_strong_signal() -> None:
    result = summarize_h1bgrader_profile(
        company_query="Databricks",
        matched_company="DATABRICKS INC",
        url=DATABRICKS_PROFILE_URL,
        body_text=DATABRICKS_PROFILE_TEXT,
        html=DATABRICKS_PROFILE_HTML,
    )

    assert result.signal == "Strong signal"
    assert result.matched_company == "DATABRICKS INC"
    assert any(
        "173 certified LCA filings and 0 denials in fiscal year 2026" in item
        for item in result.evidence
    )
    assert result.profile is not None
    assert result.profile.lca_approvals[0].model_dump() == {
        "fiscal_year": 2026,
        "counts": {
            "certified": 173,
            "certified_withdrawn": 0,
            "withdrawn": 1,
            "denied": 0,
        },
    }


def test_summarize_profile_classifies_lca_table_as_strong_signal() -> None:
    result = summarize_h1bgrader_profile(
        company_query="Databricks",
        matched_company="DATABRICKS INC",
        url=DATABRICKS_PROFILE_URL,
        body_text=DATABRICKS_PROFILE_TEXT,
        html=DATABRICKS_PROFILE_HTML,
    )

    assert result.signal == "Strong signal"
    assert any(
        "173 certified LCA filings and 0 denials in fiscal year 2026" in item
        for item in result.evidence
    )


def test_parse_h1bgrader_profile_extracts_profile_tables() -> None:
    profile = parse_h1bgrader_profile(DATABRICKS_PROFILE_HTML)

    assert [row.model_dump() for row in profile.lca_approvals[:3]] == [
        {
            "fiscal_year": 2026,
            "counts": {
                "certified": 173,
                "certified_withdrawn": 0,
                "withdrawn": 1,
                "denied": 0,
            },
        },
        {
            "fiscal_year": 2025,
            "counts": {
                "certified": 376,
                "certified_withdrawn": 9,
                "withdrawn": 0,
                "denied": 0,
            },
        },
        {
            "fiscal_year": 2024,
            "counts": {
                "certified": 292,
                "certified_withdrawn": 33,
                "withdrawn": 1,
                "denied": 0,
            },
        },
    ]
    assert [row.model_dump() for row in profile.lca_approval_rates] == [
        {"fiscal_year": 2026, "approval_rate": 100.0, "denial_rate": 0.0},
        {"fiscal_year": 2025, "approval_rate": 100.0, "denial_rate": 0.0},
        {"fiscal_year": 2019, "approval_rate": 98.55, "denial_rate": 1.45},
    ]
    assert [row.model_dump() for row in profile.uscis_approvals] == [
        {
            "fiscal_year": 2026,
            "counts": {
                "new_approvals": 0,
                "continuing_approvals": 0,
                "new_denials": 0,
                "continuing_denials": 0,
            },
        },
        {
            "fiscal_year": 2025,
            "counts": {
                "new_approvals": 70,
                "continuing_approvals": 267,
                "new_denials": 0,
                "continuing_denials": 0,
            },
        },
        {
            "fiscal_year": 2024,
            "counts": {
                "new_approvals": 81,
                "continuing_approvals": 202,
                "new_denials": 0,
                "continuing_denials": 0,
            },
        },
    ]
    assert [row.model_dump() for row in profile.uscis_approval_rates] == [
        {"fiscal_year": 2026, "approval_rate": None, "denial_rate": None},
        {"fiscal_year": 2025, "approval_rate": 100.0, "denial_rate": 0.0},
        {"fiscal_year": 2023, "approval_rate": 98.04, "denial_rate": 1.96},
    ]
    assert [row.model_dump() for row in profile.h1b_salaries] == [
        {
            "fiscal_year": 2026,
            "maximum_salary": 318781,
            "median_salary": 173732,
            "average_salary": 175681,
            "minimum_salary": 103646,
        },
        {
            "fiscal_year": 2025,
            "maximum_salary": 325000,
            "median_salary": 166962,
            "average_salary": 167569,
            "minimum_salary": 106558,
        },
        {
            "fiscal_year": 2024,
            "maximum_salary": 285500,
            "median_salary": 155000,
            "average_salary": 165360,
            "minimum_salary": 110000,
        },
    ]


def test_parse_h1bgrader_profile_extracts_salary_table_from_text() -> None:
    profile = parse_h1bgrader_profile(DATABRICKS_PROFILE_TEXT)

    assert [row.model_dump() for row in profile.h1b_salaries] == [
        {
            "fiscal_year": 2026,
            "maximum_salary": 318781,
            "median_salary": 173732,
            "average_salary": 175681,
            "minimum_salary": 103646,
        },
        {
            "fiscal_year": 2025,
            "maximum_salary": 325000,
            "median_salary": 166962,
            "average_salary": 167569,
            "minimum_salary": 106558,
        },
    ]


def test_summarize_profile_classifies_no_sponsor() -> None:
    result = summarize_h1bgrader_profile(
        company_query="No Sponsor Company",
        matched_company="NO SPONSOR COMPANY INC",
        url="https://h1bgrader.com/h1b-sponsors/no-sponsor-company-inc-test",
        body_text="No Sponsor Company INC does not sponsor H1B visas.",
    )

    assert result.signal == "No sponsor"
    assert result.profile is None
