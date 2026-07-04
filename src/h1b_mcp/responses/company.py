from h1b_mcp.matchers.job_titles import match_job_titles
from h1b_mcp.models import (
    CompanyGradeResult,
    CompanyJobSponsorshipResult,
    CompanyJobTitlesResult,
    CompanyProfile,
    CompanySalariesResult,
    CompanySponsorshipResult,
    JobSponsorshipSignal,
    JobTitleMatch,
    SponsorSignal,
)
from h1b_mcp.parsers.summary import latest_nonzero_count_row


def build_company_sponsorship_result(
    *,
    company_query: str,
    company_profile: CompanyProfile,
) -> CompanySponsorshipResult:
    """Build the compact company-level tool response from the cached raw profile."""
    evidence = company_sponsorship_evidence(company_profile)
    return CompanySponsorshipResult(
        company_query=company_query,
        matched_company=company_profile.matched_company,
        signal=classify_company_sponsorship(company_profile),
        url=company_profile.url,
        evidence=evidence or ["No clear H-1B sponsorship evidence was parsed."],
    )


def build_company_job_sponsorship_result(
    *,
    company_query: str,
    job_title: str,
    company_profile: CompanyProfile,
) -> CompanyJobSponsorshipResult:
    """Answer whether this company has title-specific sponsorship evidence."""
    matches = match_job_titles(job_title, company_profile.profile.job_titles)
    company_signal = classify_company_sponsorship(company_profile)
    signal = classify_job_sponsorship(matches, company_signal)
    evidence = company_job_sponsorship_evidence(
        job_title=job_title,
        matches=matches,
        company_signal=company_signal,
    )
    return CompanyJobSponsorshipResult(
        company_query=company_query,
        matched_company=company_profile.matched_company,
        job_title_query=job_title,
        signal=signal,
        url=company_profile.url,
        matches=matches,
        company_signal=company_signal,
        evidence=evidence,
    )


def build_company_job_titles_result(
    *,
    company_query: str,
    company_profile: CompanyProfile,
) -> CompanyJobTitlesResult:
    return CompanyJobTitlesResult(
        company_query=company_query,
        matched_company=company_profile.matched_company,
        url=company_profile.url,
        job_titles=company_profile.profile.job_titles,
    )


def build_company_salaries_result(
    *,
    company_query: str,
    company_profile: CompanyProfile,
) -> CompanySalariesResult:
    return CompanySalariesResult(
        company_query=company_query,
        matched_company=company_profile.matched_company,
        url=company_profile.url,
        salaries=company_profile.profile.h1b_salaries,
    )


def build_company_grade_result(
    *,
    company_query: str,
    company_profile: CompanyProfile,
) -> CompanyGradeResult:
    return CompanyGradeResult(
        company_query=company_query,
        matched_company=company_profile.matched_company,
        url=company_profile.url,
        grade=company_profile.profile.grade,
    )


def classify_company_sponsorship(company_profile: CompanyProfile) -> SponsorSignal:
    """Classify company evidence using only parsed structured profile data."""
    profile = company_profile.profile
    if profile.lca_approvals:
        return "Strong signal"
    if profile.uscis_approvals:
        return "Strong signal"
    if profile.job_titles:
        return "Strong signal"
    if profile.grade and profile.grade.latest_grade:
        return "Mixed signal"
    return "Weak signal"


def classify_job_sponsorship(
    matches: list[JobTitleMatch],
    company_signal: SponsorSignal,
) -> JobSponsorshipSignal:
    """Preserve the distinction between title evidence and company-only evidence."""
    if any(match.match_type == "exact" for match in matches):
        return "Exact title evidence"
    if any(match.match_type == "close" for match in matches):
        return "Close title evidence"
    if any(match.match_type == "adjacent" for match in matches):
        return "Adjacent evidence"
    if company_signal in {"Strong signal", "Mixed signal", "Weak signal"}:
        return "Company-only evidence"
    return "No evidence"


def company_sponsorship_evidence(company_profile: CompanyProfile) -> list[str]:
    """Summarize the strongest parsed rows into human-readable evidence strings."""
    profile = company_profile.profile
    evidence: list[str] = []

    if profile.lca_approvals:
        latest_lca_row = profile.lca_approvals[0]
        certified = latest_lca_row.counts.get("certified", 0)
        withdrawn = latest_lca_row.counts.get("withdrawn", 0)
        certified_withdrawn = latest_lca_row.counts.get("certified_withdrawn", 0)
        denied = latest_lca_row.counts.get("denied", 0)
        total = certified + certified_withdrawn + withdrawn + denied
        evidence.append(
            "Latest LCA table reports "
            f"{total} filings in fiscal year {latest_lca_row.fiscal_year}, "
            f"including {certified} certified and {denied} denied."
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
            "Latest non-empty USCIS table row reports "
            f"{approvals} approvals and {denials} denials "
            f"in fiscal year {uscis_row.fiscal_year}."
        )

    if profile.grade and profile.grade.latest_grade:
        grade_text = f"H1BGrader grade tab shows latest grade {profile.grade.latest_grade}"
        if profile.grade.confidence:
            grade_text += f" with {profile.grade.confidence.lower()}"
        evidence.append(f"{grade_text}.")

    if profile.job_titles:
        evidence.append(
            f"Job title table includes {len(profile.job_titles)} sponsored title rows."
        )

    return evidence


def company_job_sponsorship_evidence(
    *,
    job_title: str,
    matches: list[JobTitleMatch],
    company_signal: SponsorSignal,
) -> list[str]:
    """Explain the best title match without hiding the broader company signal."""
    if not matches:
        return [
            f"No sponsored job title row matched {job_title}.",
            f"Company-level sponsorship signal is {company_signal}.",
        ]

    best_match = matches[0]
    evidence = [
        f"Best matched sponsored title is {best_match.title} ({best_match.match_type}).",
        f"{best_match.title} has {best_match.lca_count} LCA filings in the job title table.",
        f"Company-level sponsorship signal is {company_signal}.",
    ]
    if best_match.average_salary is not None:
        evidence.append(f"Average salary for {best_match.title} is ${best_match.average_salary:,}.")
    return evidence
