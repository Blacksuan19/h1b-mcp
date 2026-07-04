from typing import Literal

from pydantic import BaseModel, Field

from h1b_mcp.models.profile import (
    AnnualCountRow,
    AnnualRateRow,
    AnnualSalaryRow,
    EmployerFilingRow,
    GradeProfile,
    H1BGraderProfile,
    JobTitleRow,
)

SponsorSignal = Literal["Strong signal", "Mixed signal", "Weak signal", "No sponsor", "Blocked"]
JobSponsorshipSignal = Literal[
    "Exact title evidence",
    "Close title evidence",
    "Adjacent evidence",
    "Company-only evidence",
    "No evidence",
    "Blocked",
]


class SponsorshipResultBase(BaseModel):
    signal: SponsorSignal
    url: str | None = None
    evidence: list[str] = Field(default_factory=list)


class SalariesResultBase(BaseModel):
    url: str | None = None
    salaries: list[AnnualSalaryRow] = Field(default_factory=list)


class AggregateEmployersResultBase(BaseModel):
    url: str | None = None
    employers: list[EmployerFilingRow] = Field(default_factory=list)


class AggregateSponsorshipResultBase(SponsorshipResultBase):
    latest_lca: AnnualCountRow | None = None
    latest_approval_rate: AnnualRateRow | None = None
    latest_salary: AnnualSalaryRow | None = None
    top_employers: list[EmployerFilingRow] = Field(default_factory=list)


class H1BLookupResult(SponsorshipResultBase):
    company_query: str
    matched_company: str | None = None
    profile: H1BGraderProfile | None = None


class CompanySponsorshipResult(SponsorshipResultBase):
    company_query: str
    matched_company: str | None = None


class JobTitleMatch(BaseModel):
    title: str
    match_type: Literal["exact", "close", "adjacent"]
    score: float
    lca_count: int
    maximum_salary: int | None = None
    average_salary: int | None = None
    minimum_salary: int | None = None


class CompanyJobSponsorshipResult(BaseModel):
    company_query: str
    matched_company: str | None = None
    job_title_query: str
    signal: JobSponsorshipSignal
    url: str | None = None
    matches: list[JobTitleMatch] = Field(default_factory=list)
    company_signal: SponsorSignal
    evidence: list[str] = Field(default_factory=list)


class CompanyJobTitlesResult(BaseModel):
    company_query: str
    matched_company: str | None = None
    url: str | None = None
    job_titles: list[JobTitleRow] = Field(default_factory=list)


class CompanySalariesResult(SalariesResultBase):
    company_query: str
    matched_company: str | None = None


class CompanyGradeResult(BaseModel):
    company_query: str
    matched_company: str | None = None
    url: str | None = None
    grade: GradeProfile | None = None


class JobTitleSponsorshipResult(AggregateSponsorshipResultBase):
    job_title_query: str
    matched_job_title: str | None = None


class JobTitleEmployersResult(AggregateEmployersResultBase):
    job_title_query: str
    matched_job_title: str | None = None


class JobTitleSalariesResult(SalariesResultBase):
    job_title_query: str
    matched_job_title: str | None = None


class LocationSponsorshipResult(AggregateSponsorshipResultBase):
    location_query: str
    matched_location: str | None = None


class LocationEmployersResult(AggregateEmployersResultBase):
    location_query: str
    matched_location: str | None = None


class LocationSalariesResult(SalariesResultBase):
    location_query: str
    matched_location: str | None = None
