from collections.abc import Callable
from dataclasses import dataclass, field
from re import Pattern
from typing import Any, Generic, TypeVar

from h1b_mcp.constants import (
    COMPANY_GRADE_TAB_SELECTOR,
    COMPANY_JOB_TITLES_TAB_SELECTOR,
    COMPANY_PROFILE_PATH_RE,
    COMPANY_SALARIES_TAB_SELECTOR,
    JOB_TITLE_PROFILE_PATH_RE,
    LOCATION_PROFILE_PATH_RE,
)
from h1b_mcp.h1bgrader.browser import get_body_text, get_page_source
from h1b_mcp.models import CompanyProfile, JobTitleProfile, LocationProfile
from h1b_mcp.parsers.aggregate import (
    extract_h1bgrader_job_title_profile,
    extract_h1bgrader_location_profile,
)
from h1b_mcp.parsers.summary import extract_h1bgrader_company_profile

TProfile = TypeVar("TProfile", CompanyProfile, JobTitleProfile, LocationProfile)


@dataclass(frozen=True)
class H1BGraderLookupSpec(Generic[TProfile]):
    """Describe the H1BGrader browser lookup parts that vary by profile type."""

    field_name: str
    search_type: str
    label: str
    path_pattern: Pattern[str]
    parse: Callable[[str, str | None, str, Any], TProfile]
    tabs_to_open: tuple[tuple[str, str], ...] = field(default_factory=tuple)


def _parse_company_profile(
    query: str,
    matched_name: str | None,
    url: str,
    sb: Any,
) -> CompanyProfile:
    return extract_h1bgrader_company_profile(
        company_query=query,
        matched_company=matched_name,
        url=url,
        body_text=get_body_text(sb),
        html=get_page_source(sb),
    )


def _parse_job_title_profile(
    query: str,
    matched_name: str | None,
    url: str,
    sb: Any,
) -> JobTitleProfile:
    return extract_h1bgrader_job_title_profile(
        job_title_query=query,
        matched_job_title=matched_name,
        url=url,
        html=get_page_source(sb),
    )


def _parse_location_profile(
    query: str,
    matched_name: str | None,
    url: str,
    sb: Any,
) -> LocationProfile:
    return extract_h1bgrader_location_profile(
        location_query=query,
        matched_location=matched_name,
        url=url,
        html=get_page_source(sb),
    )


COMPANY_LOOKUP_SPEC: H1BGraderLookupSpec[CompanyProfile] = H1BGraderLookupSpec(
    field_name="company_name",
    search_type="company",
    label="company",
    path_pattern=COMPANY_PROFILE_PATH_RE,
    parse=_parse_company_profile,
    tabs_to_open=(
        (COMPANY_SALARIES_TAB_SELECTOR, "salaries"),
        (COMPANY_GRADE_TAB_SELECTOR, "grade"),
        (COMPANY_JOB_TITLES_TAB_SELECTOR, "job titles"),
    ),
)

JOB_TITLE_LOOKUP_SPEC: H1BGraderLookupSpec[JobTitleProfile] = H1BGraderLookupSpec(
    field_name="job_title",
    search_type="job_title",
    label="job-title",
    path_pattern=JOB_TITLE_PROFILE_PATH_RE,
    parse=_parse_job_title_profile,
)

LOCATION_LOOKUP_SPEC: H1BGraderLookupSpec[LocationProfile] = H1BGraderLookupSpec(
    field_name="location",
    search_type="location",
    label="location",
    path_pattern=LOCATION_PROFILE_PATH_RE,
    parse=_parse_location_profile,
)
