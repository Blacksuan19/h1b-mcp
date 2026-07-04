from h1b_mcp.responses.aggregate import (
    build_job_title_employers_result,
    build_job_title_salaries_result,
    build_job_title_sponsorship_result,
    build_location_employers_result,
    build_location_salaries_result,
    build_location_sponsorship_result,
)
from tests.fixtures import chicago_location_profile, machine_learning_engineer_profile


def test_build_job_title_sponsorship_result_summarizes_aggregate_profile() -> None:
    profile = machine_learning_engineer_profile()

    result = build_job_title_sponsorship_result(
        job_title_query="Machine Learning Engineer",
        job_title_profile=profile,
    )

    assert result.signal == "Strong signal"
    assert result.matched_job_title == "MACHINE LEARNING ENGINEER"
    assert result.latest_lca is not None
    assert result.latest_lca.fiscal_year == 2026
    assert result.latest_salary is not None
    assert result.latest_salary.average_salary == 190500
    assert result.top_employers[0].employer_name == "Adobe INC"
    assert any("Latest job title LCA table reports 316 filings" in item for item in result.evidence)


def test_build_job_title_employers_and_salaries_results() -> None:
    profile = machine_learning_engineer_profile()

    employers = build_job_title_employers_result(
        job_title_query="Machine Learning Engineer",
        job_title_profile=profile,
        limit=1,
    )
    salaries = build_job_title_salaries_result(
        job_title_query="Machine Learning Engineer",
        job_title_profile=profile,
    )

    assert len(employers.employers) == 1
    assert employers.employers[0].employer_name == "Adobe INC"
    assert salaries.salaries[0].fiscal_year == 2026


def test_build_location_sponsorship_result_summarizes_aggregate_profile() -> None:
    profile = chicago_location_profile()

    result = build_location_sponsorship_result(
        location_query="Chicago",
        location_profile=profile,
    )

    assert result.signal == "Strong signal"
    assert result.matched_location == "CHICAGO, IL"
    assert result.latest_approval_rate is not None
    assert result.latest_approval_rate.approval_rate == 99.68
    assert result.top_employers[0].employer_name == "Adobe INC"
    assert any("Latest location LCA table reports 316 filings" in item for item in result.evidence)


def test_build_location_employers_and_salaries_results() -> None:
    profile = chicago_location_profile()

    employers = build_location_employers_result(
        location_query="Chicago",
        location_profile=profile,
        limit=1,
    )
    salaries = build_location_salaries_result(
        location_query="Chicago",
        location_profile=profile,
    )

    assert len(employers.employers) == 1
    assert employers.employers[0].employer_name == "Adobe INC"
    assert salaries.salaries[0].average_salary == 190500
