import re
from datetime import UTC, datetime

from h1b_mcp.constants import (
    NO_SPONSOR_RE,
    PROFILE_CACHE_SCHEMA_VERSION,
    YES_SPONSOR_RE,
)
from h1b_mcp.models import (
    AnnualCountRow,
    CompanyProfile,
    H1BGraderProfile,
    H1BLookupResult,
    SponsorSignal,
)
from h1b_mcp.parsers.tables import parse_h1bgrader_profile


def summarize_h1bgrader_profile(
    *,
    company_query: str,
    matched_company: str | None,
    url: str,
    body_text: str,
    html: str | None = None,
) -> H1BLookupResult:
    """Parse a fetched company page and build the older all-in-one lookup result."""
    company_profile = extract_h1bgrader_company_profile(
        company_query=company_query,
        matched_company=matched_company,
        url=url,
        body_text=body_text,
        html=html,
    )
    return build_h1b_lookup_result(
        company_query=company_query,
        company_profile=company_profile,
        body_text=body_text,
    )


def extract_h1bgrader_company_profile(
    *,
    company_query: str,
    matched_company: str | None,
    url: str,
    body_text: str,
    html: str | None = None,
    fetched_at: datetime | None = None,
) -> CompanyProfile:
    """Build the cacheable raw profile object from the current H1BGrader page state."""
    compact = re.sub(r"\s+", " ", body_text).strip()
    profile = parse_h1bgrader_profile(html or compact)

    return CompanyProfile(
        cache_schema_version=PROFILE_CACHE_SCHEMA_VERSION,
        query=company_query,
        matched_name=matched_company,
        url=url,
        fetched_at=fetched_at or datetime.now(UTC),
        profile=profile,
    )


def build_h1b_lookup_result(
    *,
    company_query: str,
    company_profile: CompanyProfile,
    body_text: str | None = None,
) -> H1BLookupResult:
    """Convert a parsed profile into the legacy sponsorship signal response."""
    evidence: list[str] = []
    profile = company_profile.profile
    compact = re.sub(r"\s+", " ", body_text or "").strip()

    if YES_SPONSOR_RE.search(compact):
        evidence.append("H1BGrader profile text says the employer sponsors H-1B visas.")
    if NO_SPONSOR_RE.search(compact):
        evidence.append("H1BGrader profile text says the employer does not sponsor H-1B visas.")
    if profile.lca_approvals:
        latest_lca_row = profile.lca_approvals[0]
        certified = latest_lca_row.counts.get("certified", 0)
        denied = latest_lca_row.counts.get("denied", 0)
        evidence.append(
            "H1BGrader LCA approvals table reports "
            f"{certified} certified LCA filings "
            f"and {denied} denials "
            f"in fiscal year {latest_lca_row.fiscal_year}."
        )
    uscis_row = latest_nonzero_count_row(profile.uscis_approvals)
    if uscis_row:
        approvals = uscis_row.counts.get("new_approvals", 0) + uscis_row.counts.get(
            "continuing_approvals", 0
        )
        denials = uscis_row.counts.get("new_denials", 0) + uscis_row.counts.get(
            "continuing_denials", 0
        )
        evidence.append(
            "H1BGrader USCIS approvals table reports "
            f"{approvals} approvals and {denials} denials "
            f"in fiscal year {uscis_row.fiscal_year}."
        )
    if profile.grade and profile.grade.latest_grade:
        grade_text = f"H1BGrader grade tab shows latest grade {profile.grade.latest_grade}"
        if profile.grade.confidence:
            grade_text += f" with {profile.grade.confidence.lower()}"
        evidence.append(f"{grade_text}.")

    signal = classify_company_profile(company_profile, evidence, body_text=compact)

    if not evidence:
        evidence.append("Company page was opened, but no clear sponsor sentence was parsed.")

    return H1BLookupResult(
        company_query=company_query,
        matched_company=company_profile.matched_name,
        signal=signal,
        url=company_profile.url,
        evidence=evidence,
        profile=profile if has_profile_data(profile) else None,
    )


def classify_company_profile(
    company_profile: CompanyProfile,
    evidence: list[str],
    *,
    body_text: str = "",
) -> SponsorSignal:
    """Prefer structured profile evidence over ambiguous marketing-page text."""
    if NO_SPONSOR_RE.search(body_text):
        return "No sponsor"
    if company_profile.profile.lca_approvals:
        return "Strong signal"
    if company_profile.profile.uscis_approvals:
        return "Strong signal"
    if company_profile.profile.job_titles:
        return "Strong signal"
    if YES_SPONSOR_RE.search(body_text):
        return "Mixed signal"
    if evidence:
        return "Weak signal"
    return "Weak signal"


def has_profile_data(profile: H1BGraderProfile) -> bool:
    """Check whether a parsed profile contains any useful table or grade data."""
    return bool(
        profile.lca_approvals
        or profile.lca_approval_rates
        or profile.uscis_approvals
        or profile.uscis_approval_rates
        or profile.h1b_salaries
        or profile.job_titles
        or profile.grade
    )


def latest_nonzero_count_row(rows: list[AnnualCountRow]) -> AnnualCountRow | None:
    """Use the newest meaningful row while tolerating current-year zero placeholders."""
    for row in rows:
        if any(row.counts.values()):
            return row
    return rows[0] if rows else None
