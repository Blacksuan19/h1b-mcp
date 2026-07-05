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

SponsorSignal = Literal["Strong signal", "Mixed signal", "Weak signal", "No sponsor"]
JobSponsorshipSignal = Literal[
    "Exact title evidence",
    "Close title evidence",
    "Adjacent evidence",
    "Company-only evidence",
    "No evidence",
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


class LCATrendsResultBase(BaseModel):
    url: str | None = None
    lca_approvals: list[AnnualCountRow] = Field(default_factory=list)
    lca_approval_rates: list[AnnualRateRow] = Field(default_factory=list)


class USCISTrendsResultBase(BaseModel):
    url: str | None = None
    uscis_approvals: list[AnnualCountRow] = Field(default_factory=list)
    uscis_approval_rates: list[AnnualRateRow] = Field(default_factory=list)


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


class CompanyLCATrendsResult(LCATrendsResultBase):
    company_query: str
    matched_company: str | None = None


class CompanyUSCISTrendsResult(USCISTrendsResultBase):
    company_query: str
    matched_company: str | None = None


class CompanyGradeResult(BaseModel):
    company_query: str
    matched_company: str | None = None
    url: str | None = None
    grade: GradeProfile | None = None


class CompanyRoleSponsorshipContextResult(BaseModel):
    company_query: str
    matched_company: str | None = None
    company_url: str | None = None
    company_signal: SponsorSignal
    company_evidence: list[str] = Field(default_factory=list)
    job_title_query: str
    matched_job_title: str | None = None
    job_title_url: str | None = None
    company_role_signal: JobSponsorshipSignal
    company_role_matches: list[JobTitleMatch] = Field(default_factory=list)
    company_role_evidence: list[str] = Field(default_factory=list)
    market_signal: SponsorSignal
    market_evidence: list[str] = Field(default_factory=list)
    market_latest_lca: AnnualCountRow | None = None
    market_latest_approval_rate: AnnualRateRow | None = None
    market_latest_salary: AnnualSalaryRow | None = None
    market_top_employers: list[EmployerFilingRow] = Field(default_factory=list)


class JobTitleSponsorshipResult(AggregateSponsorshipResultBase):
    job_title_query: str
    matched_job_title: str | None = None


class JobTitleEmployersResult(AggregateEmployersResultBase):
    job_title_query: str
    matched_job_title: str | None = None


class JobTitleSalariesResult(SalariesResultBase):
    job_title_query: str
    matched_job_title: str | None = None


class JobTitleLCATrendsResult(LCATrendsResultBase):
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


class LocationLCATrendsResult(LCATrendsResultBase):
    location_query: str
    matched_location: str | None = None
