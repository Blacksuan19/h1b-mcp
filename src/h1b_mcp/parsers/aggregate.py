from datetime import UTC, datetime

from h1b_mcp.constants import PROFILE_CACHE_SCHEMA_VERSION
from h1b_mcp.models import (
    EmployerFilingRow,
    H1BGraderAggregateProfile,
    JobTitleProfile,
    LocationProfile,
)
from h1b_mcp.parsers.tables import (
    LCA_COUNT_COLUMNS,
    extract_html_tables,
    find_table,
    find_table_with_headers,
    parse_count_table,
    parse_int_cell,
    parse_rate_table,
    parse_salary_table,
)


def extract_h1bgrader_job_title_profile(
    *,
    job_title_query: str,
    matched_job_title: str | None,
    url: str,
    html: str,
    fetched_at: datetime | None = None,
) -> JobTitleProfile:
    """Build a cacheable job-title profile from H1BGrader's job-title page."""
    return JobTitleProfile(
        cache_schema_version=PROFILE_CACHE_SCHEMA_VERSION,
        query=job_title_query,
        matched_name=matched_job_title,
        url=url,
        fetched_at=fetched_at or datetime.now(UTC),
        profile=parse_h1bgrader_aggregate_profile(html),
    )


def extract_h1bgrader_location_profile(
    *,
    location_query: str,
    matched_location: str | None,
    url: str,
    html: str,
    fetched_at: datetime | None = None,
) -> LocationProfile:
    """Build a cacheable location profile from H1BGrader's city page."""
    return LocationProfile(
        cache_schema_version=PROFILE_CACHE_SCHEMA_VERSION,
        query=location_query,
        matched_name=matched_location,
        url=url,
        fetched_at=fetched_at or datetime.now(UTC),
        profile=parse_h1bgrader_aggregate_profile(html),
    )


def parse_h1bgrader_aggregate_profile(html: str) -> H1BGraderAggregateProfile:
    """Parse the shared job-title/location H1BGrader result-page table layout."""
    tables = extract_html_tables(html)
    return H1BGraderAggregateProfile(
        lca_approvals=parse_count_table(
            find_table(tables, "H1B LCA Approvals, Denials"),
            LCA_COUNT_COLUMNS,
        ),
        lca_approval_rates=parse_rate_table(find_table(tables, "H1B LCA Approval & Denial Rates")),
        h1b_salaries=parse_salary_table(find_table(tables, "H1B Salaries")),
        employers=parse_employer_table(
            find_table_with_headers(tables, ("Employer Name", "H1B LCA Filings Count"))
        ),
    )


def parse_employer_table(table: list[list[str]]) -> list[EmployerFilingRow]:
    """Parse employer filing-count rows from shared aggregate pages."""
    rows: list[EmployerFilingRow] = []
    for row in table:
        if len(row) < 2 or row[0] == "Employer Name":
            continue
        try:
            count = parse_int_cell(row[1])
        except ValueError:
            continue
        rows.append(EmployerFilingRow(employer_name=row[0], lca_count=count))
    return rows
