from h1b_mcp.matchers.job_titles import match_job_titles
from h1b_mcp.responses.company import (
    build_company_grade_result,
    build_company_job_sponsorship_result,
    build_company_job_titles_result,
    build_company_lca_trends_result,
    build_company_role_sponsorship_context_result,
    build_company_salaries_result,
    build_company_sponsorship_result,
    build_company_uscis_trends_result,
)
from tests.fixtures import databricks_company_profile, machine_learning_engineer_profile


def test_build_company_sponsorship_result_is_compact() -> None:
    company_profile = databricks_company_profile()
    result = build_company_sponsorship_result(
        company_query="Databricks",
        company_profile=company_profile,
    )

    assert result.signal == "Strong signal"
    assert result.matched_company == "DATABRICKS INC"
    assert any("Latest LCA table reports 174 filings" in item for item in result.evidence)
    assert "profile" not in result.model_dump(mode="json")


def test_build_company_job_sponsorship_result_matches_exact_title() -> None:
    company_profile = databricks_company_profile()
    result = build_company_job_sponsorship_result(
        company_query="Databricks",
        job_title="Software Engineer",
        company_profile=company_profile,
    )

    assert result.signal == "Exact title evidence"
    assert result.matches[0].title == "Software Engineer"
    assert result.matches[0].lca_count == 33
    assert result.company_signal == "Strong signal"


def test_build_company_job_sponsorship_result_matches_adjacent_title() -> None:
    company_profile = databricks_company_profile()
    result = build_company_job_sponsorship_result(
        company_query="Databricks",
        job_title="Machine Learning Engineer",
        company_profile=company_profile,
    )

    assert result.signal in {"Close title evidence", "Adjacent evidence"}
    assert result.matches
    assert result.company_signal == "Strong signal"


def test_build_company_job_sponsorship_result_returns_company_only_without_title_match() -> None:
    company_profile = databricks_company_profile()
    result = build_company_job_sponsorship_result(
        company_query="Databricks",
        job_title="Immigration Counsel",
        company_profile=company_profile,
    )

    assert result.signal == "Company-only evidence"
    assert result.matches == []
    assert result.company_signal == "Strong signal"


def test_build_company_profile_slices() -> None:
    company_profile = databricks_company_profile()

    job_titles = build_company_job_titles_result(
        company_query="Databricks",
        company_profile=company_profile,
    )
    salaries = build_company_salaries_result(
        company_query="Databricks",
        company_profile=company_profile,
    )
    grade = build_company_grade_result(
        company_query="Databricks",
        company_profile=company_profile,
    )

    assert job_titles.job_titles[0].title == "Software Engineer"
    assert salaries.salaries[0].fiscal_year == 2026
    assert grade.grade is not None
    assert grade.grade.latest_grade == "A"


def test_build_company_lca_trends_result_returns_trend_rows() -> None:
    company_profile = databricks_company_profile()

    result = build_company_lca_trends_result(
        company_query="Databricks",
        company_profile=company_profile,
    )

    assert result.company_query == "Databricks"
    assert result.matched_company == "DATABRICKS INC"
    assert result.lca_approvals[0].fiscal_year == 2026
    assert result.lca_approval_rates[0].approval_rate == 100.0


def test_build_company_uscis_trends_result_returns_trend_rows() -> None:
    company_profile = databricks_company_profile()

    result = build_company_uscis_trends_result(
        company_query="Databricks",
        company_profile=company_profile,
    )

    assert result.company_query == "Databricks"
    assert result.matched_company == "DATABRICKS INC"
    assert result.uscis_approvals[0].fiscal_year == 2026
    assert result.uscis_approvals[1].counts["new_approvals"] == 70
    assert result.uscis_approval_rates[1].approval_rate == 100.0


def test_build_company_role_sponsorship_context_combines_company_and_market_data() -> None:
    company_profile = databricks_company_profile()
    job_title_profile = machine_learning_engineer_profile()

    result = build_company_role_sponsorship_context_result(
        company_query="Databricks",
        job_title_query="Machine Learning Engineer",
        company_profile=company_profile,
        job_title_profile=job_title_profile,
    )

    assert result.company_query == "Databricks"
    assert result.matched_company == "DATABRICKS INC"
    assert result.job_title_query == "Machine Learning Engineer"
    assert result.matched_job_title == "MACHINE LEARNING ENGINEER"
    assert result.company_signal == "Strong signal"
    assert result.company_role_signal in {"Close title evidence", "Adjacent evidence"}
    assert result.market_signal == "Strong signal"
    assert result.market_top_employers[0].employer_name == "Adobe INC"


def test_match_job_titles_orders_exact_before_adjacent() -> None:
    company_profile = databricks_company_profile()

    matches = match_job_titles("Software Engineer", company_profile.profile.job_titles)

    assert matches[0].title == "Software Engineer"
    assert matches[0].match_type == "exact"
    assert matches[1].title == "Sr Software Engineer"
    assert matches[1].match_type == "close"
