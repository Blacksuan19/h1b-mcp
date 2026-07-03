import re

from h1b_mcp.constants import (
    FISCAL_YEAR_RE,
    GRADE_RE,
    LCA_COUNT_RE,
    NO_SPONSOR_RE,
    YES_SPONSOR_RE,
)
from h1b_mcp.models import H1BGraderProfile, H1BLookupResult, SponsorSignal
from h1b_mcp.parsers.tables import parse_h1bgrader_profile


def summarize_h1bgrader_profile(
    *,
    company_query: str,
    matched_company: str | None,
    url: str,
    body_text: str,
    html: str | None = None,
) -> H1BLookupResult:
    compact = re.sub(r"\s+", " ", body_text).strip()
    evidence: list[str] = []
    caveats = ["Company-level history does not prove this specific role sponsors."]
    profile = parse_h1bgrader_profile(html or compact)

    lca_match = LCA_COUNT_RE.search(compact)
    fy_match = FISCAL_YEAR_RE.search(compact)
    grade_match = GRADE_RE.search(compact)

    if YES_SPONSOR_RE.search(compact):
        evidence.append("H1BGrader profile text says the employer sponsors H-1B visas.")
    if NO_SPONSOR_RE.search(compact):
        evidence.append("H1BGrader profile text says the employer does not sponsor H-1B visas.")
    if lca_match:
        year_suffix = f" in fiscal year {fy_match.group(1)}" if fy_match else ""
        evidence.append(f"H1BGrader text reports {lca_match.group(1)} LCA filings{year_suffix}.")
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
    if grade_match:
        evidence.append(f"H1BGrader text shows a grade or score of {grade_match.group(1).upper()}.")

    signal = classify_signal(compact, evidence)

    if not evidence:
        evidence.append("Company page was opened, but no clear sponsor sentence was parsed.")
        caveats.append("Open the returned URL manually before treating this as a sponsor signal.")

    return H1BLookupResult(
        company_query=company_query,
        matched_company=matched_company,
        signal=signal,
        url=url,
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


def has_profile_data(profile: H1BGraderProfile) -> bool:
    return bool(
        profile.lca_approvals
        or profile.lca_approval_rates
        or profile.uscis_approvals
        or profile.uscis_approval_rates
    )
