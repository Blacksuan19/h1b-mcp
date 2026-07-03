import re
from datetime import UTC, datetime

from h1b_mcp.constants import (
    FISCAL_YEAR_RE,
    GRADE_RE,
    LCA_COUNT_RE,
    NO_SPONSOR_RE,
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
    company_profile = extract_h1bgrader_company_profile(
        company_query=company_query,
        matched_company=matched_company,
        url=url,
        body_text=body_text,
        html=html,
    )
    return build_h1b_lookup_result(company_query=company_query, company_profile=company_profile)


def extract_h1bgrader_company_profile(
    *,
    company_query: str,
    matched_company: str | None,
    url: str,
    body_text: str,
    html: str | None = None,
    fetched_at: datetime | None = None,
) -> CompanyProfile:
    compact = re.sub(r"\s+", " ", body_text).strip()
    profile = parse_h1bgrader_profile(html or compact)

    lca_match = LCA_COUNT_RE.search(compact)
    fy_match = FISCAL_YEAR_RE.search(compact)
    grade_match = GRADE_RE.search(compact)

    sponsor_status = None
    if NO_SPONSOR_RE.search(compact):
        sponsor_status = "does_not_sponsor"
    elif YES_SPONSOR_RE.search(compact):
        sponsor_status = "sponsors"

    return CompanyProfile(
        company_query=company_query,
        matched_company=matched_company,
        url=url,
        fetched_at=fetched_at or datetime.now(UTC),
        sponsor_status=sponsor_status,
        reported_lca_count=parse_reported_lca_count(lca_match),
        reported_lca_fiscal_year=int(fy_match.group(1)) if fy_match else None,
        grade=grade_match.group(1).upper() if grade_match else None,
        profile=profile,
    )


def build_h1b_lookup_result(
    *, company_query: str, company_profile: CompanyProfile
) -> H1BLookupResult:
    evidence: list[str] = []
    caveats = ["Company-level history does not prove this specific role sponsors."]
    profile = company_profile.profile

    if company_profile.sponsor_status == "sponsors":
        evidence.append("H1BGrader profile text says the employer sponsors H-1B visas.")
    if company_profile.sponsor_status == "does_not_sponsor":
        evidence.append("H1BGrader profile text says the employer does not sponsor H-1B visas.")
    if company_profile.reported_lca_count is not None:
        year_suffix = (
            f" in fiscal year {company_profile.reported_lca_fiscal_year}"
            if company_profile.reported_lca_fiscal_year
            else ""
        )
        evidence.append(
            f"H1BGrader text reports {company_profile.reported_lca_count:,} "
            f"LCA filings{year_suffix}."
        )
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
    if company_profile.grade:
        evidence.append(f"H1BGrader text shows a grade or score of {company_profile.grade}.")

    signal = classify_company_profile(company_profile, evidence)

    if not evidence:
        evidence.append("Company page was opened, but no clear sponsor sentence was parsed.")
        caveats.append("Open the returned URL manually before treating this as a sponsor signal.")

    return H1BLookupResult(
        company_query=company_query,
        matched_company=company_profile.matched_company,
        signal=signal,
        source=company_profile.source,
        url=company_profile.url,
        evidence=evidence,
        caveats=caveats,
        profile=profile if has_profile_data(profile) else None,
    )


def classify_signal(body_text: str, evidence: list[str]) -> SponsorSignal:
    if NO_SPONSOR_RE.search(body_text):
        return "No sponsor"
    if YES_SPONSOR_RE.search(body_text) and LCA_COUNT_RE.search(body_text):
        return "Strong signal"
    if any("certified LCA filings" in item for item in evidence):
        return "Strong signal"
    if YES_SPONSOR_RE.search(body_text) or LCA_COUNT_RE.search(body_text):
        return "Mixed signal"
    if evidence:
        return "Weak signal"
    return "Weak signal"


def classify_company_profile(
    company_profile: CompanyProfile,
    evidence: list[str],
) -> SponsorSignal:
    if company_profile.sponsor_status == "does_not_sponsor":
        return "No sponsor"
    if company_profile.profile.lca_approvals:
        return "Strong signal"
    if (
        company_profile.sponsor_status == "sponsors"
        and company_profile.reported_lca_count is not None
    ):
        return "Strong signal"
    if (
        company_profile.sponsor_status == "sponsors"
        or company_profile.reported_lca_count is not None
    ):
        return "Mixed signal"
    if evidence:
        return "Weak signal"
    return "Weak signal"


def has_profile_data(profile: H1BGraderProfile) -> bool:
    return bool(
        profile.lca_approvals
        or profile.lca_approval_rates
        or profile.uscis_approvals
        or profile.uscis_approval_rates
    )


def parse_reported_lca_count(match: re.Match[str] | None) -> int | None:
    if not match:
        return None
    return int(match.group(1).replace(",", ""))


def latest_nonzero_count_row(rows: list[AnnualCountRow]) -> AnnualCountRow | None:
    for row in rows:
        if any(row.counts.values()):
            return row
    return rows[0] if rows else None
