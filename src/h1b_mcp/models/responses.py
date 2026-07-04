from typing import Literal

from pydantic import BaseModel, Field

from h1b_mcp.models.profile import (
    AnnualSalaryRow,
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


class H1BLookupResult(BaseModel):
    company_query: str
    matched_company: str | None = None
    signal: SponsorSignal
    url: str | None = None
    evidence: list[str] = Field(default_factory=list)
    profile: H1BGraderProfile | None = None


class CompanySponsorshipResult(BaseModel):
    company_query: str
    matched_company: str | None = None
    signal: SponsorSignal
    url: str | None = None
    evidence: list[str] = Field(default_factory=list)


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


class CompanySalariesResult(BaseModel):
    company_query: str
    matched_company: str | None = None
    url: str | None = None
    salaries: list[AnnualSalaryRow] = Field(default_factory=list)


class CompanyGradeResult(BaseModel):
    company_query: str
    matched_company: str | None = None
    url: str | None = None
    grade: GradeProfile | None = None
