from typing import TypeVar

from h1b_mcp.models import (
    AnnualCountRow,
    AnnualRateRow,
    AnnualSalaryRow,
    JobTitleEmployersResult,
    JobTitleProfile,
    JobTitleSalariesResult,
    JobTitleSponsorshipResult,
    LocationEmployersResult,
    LocationProfile,
    LocationSalariesResult,
    LocationSponsorshipResult,
    SponsorSignal,
)

TAggregateProfile = TypeVar("TAggregateProfile", JobTitleProfile, LocationProfile)


def build_job_title_sponsorship_result(
    *,
    job_title_query: str,
    job_title_profile: JobTitleProfile,
    employer_limit: int = 10,
) -> JobTitleSponsorshipResult:
    latest_lca = latest_lca_row(job_title_profile)
    latest_rate = latest_rate_row(job_title_profile)
    latest_salary = latest_salary_row(job_title_profile)
    top_employers = job_title_profile.profile.employers[:bounded_limit(employer_limit)]
    return JobTitleSponsorshipResult(
        job_title_query=job_title_query,
        matched_job_title=job_title_profile.matched_name,
        signal=classify_aggregate_sponsorship(job_title_profile),
        url=job_title_profile.url,
        evidence=aggregate_sponsorship_evidence(
            profile=job_title_profile,
            label="job title",
        ),
        latest_lca=latest_lca,
        latest_approval_rate=latest_rate,
        latest_salary=latest_salary,
        top_employers=top_employers,
    )


def build_job_title_employers_result(
    *,
    job_title_query: str,
    job_title_profile: JobTitleProfile,
    limit: int = 20,
) -> JobTitleEmployersResult:
    return JobTitleEmployersResult(
        job_title_query=job_title_query,
        matched_job_title=job_title_profile.matched_name,
        url=job_title_profile.url,
        employers=job_title_profile.profile.employers[:bounded_limit(limit)],
    )


def build_job_title_salaries_result(
    *,
    job_title_query: str,
    job_title_profile: JobTitleProfile,
) -> JobTitleSalariesResult:
    return JobTitleSalariesResult(
        job_title_query=job_title_query,
        matched_job_title=job_title_profile.matched_name,
        url=job_title_profile.url,
        salaries=job_title_profile.profile.h1b_salaries,
    )


def build_location_sponsorship_result(
    *,
    location_query: str,
    location_profile: LocationProfile,
    employer_limit: int = 10,
) -> LocationSponsorshipResult:
    latest_lca = latest_lca_row(location_profile)
    latest_rate = latest_rate_row(location_profile)
    latest_salary = latest_salary_row(location_profile)
    top_employers = location_profile.profile.employers[:bounded_limit(employer_limit)]
    return LocationSponsorshipResult(
        location_query=location_query,
        matched_location=location_profile.matched_name,
        signal=classify_aggregate_sponsorship(location_profile),
        url=location_profile.url,
        evidence=aggregate_sponsorship_evidence(
            profile=location_profile,
            label="location",
        ),
        latest_lca=latest_lca,
        latest_approval_rate=latest_rate,
        latest_salary=latest_salary,
        top_employers=top_employers,
    )


def build_location_employers_result(
    *,
    location_query: str,
    location_profile: LocationProfile,
    limit: int = 20,
) -> LocationEmployersResult:
    return LocationEmployersResult(
        location_query=location_query,
        matched_location=location_profile.matched_name,
        url=location_profile.url,
        employers=location_profile.profile.employers[:bounded_limit(limit)],
    )


def build_location_salaries_result(
    *,
    location_query: str,
    location_profile: LocationProfile,
) -> LocationSalariesResult:
    return LocationSalariesResult(
        location_query=location_query,
        matched_location=location_profile.matched_name,
        url=location_profile.url,
        salaries=location_profile.profile.h1b_salaries,
    )


def classify_aggregate_sponsorship(profile: TAggregateProfile) -> SponsorSignal:
    """Classify market-level sponsorship signal from aggregate H1BGrader tables."""
    latest_lca = latest_lca_row(profile)
    if latest_lca and total_lca_filings(latest_lca) > 0:
        return "Strong signal"
    if profile.profile.employers:
        return "Strong signal"
    if profile.profile.h1b_salaries or profile.profile.lca_approval_rates:
        return "Mixed signal"
    return "Weak signal"


def aggregate_sponsorship_evidence(
    *,
    profile: TAggregateProfile,
    label: str,
) -> list[str]:
    """Summarize the strongest aggregate rows into human-readable evidence."""
    evidence: list[str] = []

    latest_lca = latest_lca_row(profile)
    if latest_lca:
        total = total_lca_filings(latest_lca)
        certified = latest_lca.counts.get("certified", 0)
        denied = latest_lca.counts.get("denied", 0)
        evidence.append(
            f"Latest {label} LCA table reports {total} filings in fiscal year "
            f"{latest_lca.fiscal_year}, including {certified} certified and {denied} denied."
        )

    latest_rate = latest_rate_row(profile)
    if latest_rate:
        rate_text = f"Latest approval-rate row is fiscal year {latest_rate.fiscal_year}"
        if latest_rate.approval_rate is not None:
            rate_text += f" with {latest_rate.approval_rate:.2f}% approval"
        if latest_rate.denial_rate is not None:
            rate_text += f" and {latest_rate.denial_rate:.2f}% denial"
        evidence.append(f"{rate_text}.")

    latest_salary = latest_salary_row(profile)
    if latest_salary and latest_salary.average_salary is not None:
        evidence.append(
            f"Latest salary table average is ${latest_salary.average_salary:,} "
            f"in fiscal year {latest_salary.fiscal_year}."
        )

    if profile.profile.employers:
        top_employer = profile.profile.employers[0]
        evidence.append(
            f"Employer table includes {len(profile.profile.employers)} employers; "
            f"top employer is {top_employer.employer_name} with "
            f"{top_employer.lca_count} LCA filings."
        )

    return evidence or ["No clear H-1B sponsorship evidence was parsed."]


def latest_lca_row(profile: TAggregateProfile) -> AnnualCountRow | None:
    return profile.profile.lca_approvals[0] if profile.profile.lca_approvals else None


def latest_rate_row(profile: TAggregateProfile) -> AnnualRateRow | None:
    return profile.profile.lca_approval_rates[0] if profile.profile.lca_approval_rates else None


def latest_salary_row(profile: TAggregateProfile) -> AnnualSalaryRow | None:
    return profile.profile.h1b_salaries[0] if profile.profile.h1b_salaries else None


def total_lca_filings(row: AnnualCountRow) -> int:
    return sum(row.counts.values())


def bounded_limit(limit: int, *, default: int = 20, maximum: int = 100) -> int:
    if limit <= 0:
        return default
    return min(limit, maximum)
