from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

TParsedProfile = TypeVar("TParsedProfile", bound=BaseModel)


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


class JobTitleRow(BaseModel):
    title: str
    lca_count: int
    maximum_salary: int | None = None
    average_salary: int | None = None
    minimum_salary: int | None = None


class EmployerFilingRow(BaseModel):
    employer_name: str
    lca_count: int


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
    job_titles: list[JobTitleRow] = Field(default_factory=list)
    grade: GradeProfile | None = None


class CachedProfile(BaseModel, Generic[TParsedProfile]):
    cache_schema_version: int = 0
    query: str
    matched_name: str | None = None
    url: str
    fetched_at: datetime


class CompanyProfile(CachedProfile[H1BGraderProfile]):
    profile: H1BGraderProfile = Field(default_factory=H1BGraderProfile)


class H1BGraderAggregateProfile(BaseModel):
    lca_approvals: list[AnnualCountRow] = Field(default_factory=list)
    lca_approval_rates: list[AnnualRateRow] = Field(default_factory=list)
    h1b_salaries: list[AnnualSalaryRow] = Field(default_factory=list)
    employers: list[EmployerFilingRow] = Field(default_factory=list)


class JobTitleProfile(CachedProfile[H1BGraderAggregateProfile]):
    profile: H1BGraderAggregateProfile = Field(default_factory=H1BGraderAggregateProfile)


class LocationProfile(CachedProfile[H1BGraderAggregateProfile]):
    profile: H1BGraderAggregateProfile = Field(default_factory=H1BGraderAggregateProfile)
