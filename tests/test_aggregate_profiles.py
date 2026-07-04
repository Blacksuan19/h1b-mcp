from datetime import UTC, datetime

from h1b_mcp.constants import PROFILE_CACHE_SCHEMA_VERSION
from h1b_mcp.parsers.aggregate import (
    extract_h1bgrader_job_title_profile,
    extract_h1bgrader_location_profile,
)
from tests.fixtures import SEARCH_RESULT_HTML, SEARCH_RESULT_URL


def test_parse_h1bgrader_job_title_profile_extracts_shared_tables() -> None:
    profile = extract_h1bgrader_job_title_profile(
        job_title_query="Machine Learning Engineer",
        matched_job_title="MACHINE LEARNING ENGINEER",
        url=SEARCH_RESULT_URL,
        html=SEARCH_RESULT_HTML,
        fetched_at=datetime(2026, 7, 4, tzinfo=UTC),
    )

    assert profile.cache_schema_version == PROFILE_CACHE_SCHEMA_VERSION
    assert profile.query == "Machine Learning Engineer"
    assert profile.matched_name == "MACHINE LEARNING ENGINEER"
    assert profile.profile.lca_approvals[0].model_dump() == {
        "fiscal_year": 2026,
        "counts": {
            "certified": 290,
            "certified_withdrawn": 20,
            "withdrawn": 5,
            "denied": 1,
        },
    }
    assert profile.profile.lca_approval_rates[0].model_dump() == {
        "fiscal_year": 2026,
        "approval_rate": 99.68,
        "denial_rate": 0.32,
    }
    assert profile.profile.h1b_salaries[0].model_dump() == {
        "fiscal_year": 2026,
        "maximum_salary": 320000,
        "median_salary": 180000,
        "average_salary": 190500,
        "minimum_salary": 110000,
    }
    assert [row.model_dump() for row in profile.profile.employers] == [
        {"employer_name": "Adobe INC", "lca_count": 126},
        {"employer_name": "Databricks INC", "lca_count": 45},
    ]


def test_parse_h1bgrader_location_profile_extracts_shared_tables() -> None:
    profile = extract_h1bgrader_location_profile(
        location_query="Chicago",
        matched_location="CHICAGO, IL",
        url="https://h1bgrader.com/cities/chicago-illinois-1ok85pwzkd",
        html=SEARCH_RESULT_HTML,
        fetched_at=datetime(2026, 7, 4, tzinfo=UTC),
    )

    assert profile.cache_schema_version == PROFILE_CACHE_SCHEMA_VERSION
    assert profile.query == "Chicago"
    assert profile.matched_name == "CHICAGO, IL"
    assert profile.profile.employers[0].employer_name == "Adobe INC"
    assert profile.profile.h1b_salaries[0].average_salary == 190500
