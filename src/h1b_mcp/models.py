from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

SponsorSignal = Literal["Strong signal", "Mixed signal", "Weak signal", "No sponsor", "Blocked"]
SponsorTextStatus = Literal["sponsors", "does_not_sponsor"]


class AnnualCountRow(BaseModel):
    fiscal_year: int
    counts: dict[str, int] = Field(default_factory=dict)


class AnnualRateRow(BaseModel):
    fiscal_year: int
    approval_rate: float | None = None
    denial_rate: float | None = None


class AnnualSalaryRow(BaseModel):
    fiscal_year: int
    maximum_salary: int | None = None
    median_salary: int | None = None
    average_salary: int | None = None
    minimum_salary: int | None = None


class AnnualGradeRow(BaseModel):
    fiscal_year: int
    grade: str
    period: str | None = None


class GradeInsight(BaseModel):
    title: str
    description: str
    score: int | None = None
    score_max: int | None = None
    status: str | None = None
    sentiment: str | None = None


class GradeProfile(BaseModel):
    latest_grade: str | None = None
    confidence: str | None = None
    annual_grades: list[AnnualGradeRow] = Field(default_factory=list)
    insights: list[GradeInsight] = Field(default_factory=list)


class H1BGraderProfile(BaseModel):
    lca_approvals: list[AnnualCountRow] = Field(default_factory=list)
    lca_approval_rates: list[AnnualRateRow] = Field(default_factory=list)
    uscis_approvals: list[AnnualCountRow] = Field(default_factory=list)
    uscis_approval_rates: list[AnnualRateRow] = Field(default_factory=list)
    h1b_salaries: list[AnnualSalaryRow] = Field(default_factory=list)
    grade: GradeProfile | None = None


class CompanyProfile(BaseModel):
    cache_schema_version: int = 0
    company_query: str
    matched_company: str | None = None
    url: str
    fetched_at: datetime
    sponsor_status: SponsorTextStatus | None = None
    reported_lca_count: int | None = None
    reported_lca_fiscal_year: int | None = None
    grade: str | None = None
    profile: H1BGraderProfile = Field(default_factory=H1BGraderProfile)


class H1BLookupResult(BaseModel):
    company_query: str
    matched_company: str | None = None
    signal: SponsorSignal
    url: str | None = None
    evidence: list[str] = Field(default_factory=list)
    profile: H1BGraderProfile | None = None


class H1BGraderBlockedError(RuntimeError):
    def __init__(self, message: str, *, url: str | None = None) -> None:
        super().__init__(message)
        self.url = url
