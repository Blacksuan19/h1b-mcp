import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path

from h1b_mcp.cache import CompanyProfileCache
from h1b_mcp.models import CompanyProfile
from h1b_mcp.parsers.summary import summarize_h1bgrader_profile
from h1b_mcp.parsers.tables import parse_h1bgrader_profile
from h1b_mcp.service import H1BGraderService
from h1b_mcp.settings import Settings
from h1b_mcp.utils import (
    best_company_match,
    is_challenge_page,
    normalize_company_name,
    seleniumbase_timeout_multiplier,
)

DATABRICKS_PROFILE_URL = "https://h1bgrader.com/h1b-sponsors/databricks-inc-nokpn1vn04"
DATABRICKS_PROFILE_TEXT = (
    "Databricks INC H1B Sponsorship Data "
    "Yes, Databricks INC sponsors H1B visas. "
    "H1B LCA Approvals, Denials Fiscal Year* Certified Certified Withd. "
    "Withdrawn Denied 2026 173 - 1 - 2025 376 9 - - 2024 292 33 1 - "
    "2023 211 26 1 - 2022 241 4 - - 2021 170 2 3 - 2020 68 3 - - "
    "2019 64 4 2 1 2018 39 4 3 - 2017 38 7 - - "
    "H1B LCA Approval & Denial Rates Fiscal Year* Approval (%) Denial (%) "
    "2026 100.00% 0.00% 2025 100.00% 0.00% 2019 98.55% 1.45% "
    "Latest H1B Job Titles sponsored by Databricks INC in 2026 (H1B LCAs) "
    "H1B Job Title LCA Count Maximum Salary Average Salary Minimum Salary "
    "Software Engineer 33 $187,741 $160,905 $131,997 "
    "Sr Software Engineer 27 $226,138 $192,758 $157,000"
)
DATABRICKS_PROFILE_HTML = """
<html>
  <body>
    <h1>Databricks INC H1B Sponsorship Data</h1>
    <p>Yes, Databricks INC sponsors H1B visas.</p>
    <table>
      <tr><th colspan="5">H1B LCA Approvals, Denials</th></tr>
      <tr>
        <th>Fiscal Year*</th><th>Certified</th><th>Certified Withd.</th>
        <th>Withdrawn</th><th>Denied</th>
      </tr>
      <tr><td>2026</td><td>173</td><td>-</td><td>1</td><td>-</td></tr>
      <tr><td>2025</td><td>376</td><td>9</td><td>-</td><td>-</td></tr>
      <tr><td>2024</td><td>292</td><td>33</td><td>1</td><td>-</td></tr>
    </table>
    <table>
      <tr><th colspan="3">H1B LCA Approval &amp; Denial Rates</th></tr>
      <tr><th>Fiscal Year*</th><th>Approval (%)</th><th>Denial (%)</th></tr>
      <tr><td>2026</td><td>100.00%</td><td>0.00%</td></tr>
      <tr><td>2025</td><td>100.00%</td><td>0.00%</td></tr>
      <tr><td>2019</td><td>98.55%</td><td>1.45%</td></tr>
    </table>
    <table>
      <tr><th colspan="5">USCIS H1B Approvals, Denials</th></tr>
      <tr>
        <th>Fiscal Year*</th><th>New Approvals</th><th>Cont. Approvals</th>
        <th>New Denials</th><th>Cont. Denials</th>
      </tr>
      <tr><td>2026</td><td>-</td><td>-</td><td>-</td><td>-</td></tr>
      <tr><td>2025</td><td>70</td><td>267</td><td>-</td><td>-</td></tr>
      <tr><td>2024</td><td>81</td><td>202</td><td>-</td><td>-</td></tr>
    </table>
    <table>
      <tr><th colspan="3">USCIS H1B Approval &amp; Denial Rates</th></tr>
      <tr><th>Fiscal Year*</th><th>Approval (%)</th><th>Denial (%)</th></tr>
      <tr><td>2026</td><td>N/A</td><td>N/A</td></tr>
      <tr><td>2025</td><td>100.00%</td><td>0.00%</td></tr>
      <tr><td>2023</td><td>98.04%</td><td>1.96%</td></tr>
    </table>
  </body>
</html>
"""


class FakeProfileFetcher:
    def __init__(self, profile: CompanyProfile) -> None:
        self.profile = profile
        self.calls: list[str] = []
        self.logger: object | None = None

    async def fetch_company_profile(
        self,
        company_name: str,
        *,
        logger: object | None = None,
    ) -> CompanyProfile:
        self.calls.append(company_name)
        self.logger = logger
        return self.profile


class FakeLogSink:
    def __init__(self) -> None:
        self.messages: list[tuple[str, str]] = []

    async def debug(self, message: str) -> None:
        self.messages.append(("debug", message))

    async def info(self, message: str) -> None:
        self.messages.append(("info", message))

    async def warning(self, message: str) -> None:
        self.messages.append(("warning", message))

    async def error(self, message: str) -> None:
        self.messages.append(("error", message))


def cache_settings(tmp_path: Path, *, cache_ttl_seconds: int = 60 * 60) -> Settings:
    return Settings(
        profile_dir=tmp_path / "browser-profile",
        cache_dir=tmp_path / "company-cache",
        cache_ttl_seconds=cache_ttl_seconds,
    )


def databricks_company_profile(*, fetched_at: datetime | None = None) -> CompanyProfile:
    return CompanyProfile(
        company_query="Databricks",
        matched_company="DATABRICKS INC",
        url=DATABRICKS_PROFILE_URL,
        fetched_at=fetched_at or datetime.now(UTC),
        sponsor_status="sponsors",
        profile=parse_h1bgrader_profile(DATABRICKS_PROFILE_HTML),
    )


def test_normalize_company_name_removes_common_suffixes() -> None:
    assert normalize_company_name("Databricks, Inc.") == "databricks"


def test_best_company_match_prefers_exact_normalized_match() -> None:
    match = best_company_match(
        "Databricks",
        [
            ("Data Inc", "https://h1bgrader.com/h1b-sponsors/data-inc-abc123"),
            ("Databricks Inc", DATABRICKS_PROFILE_URL),
        ],
    )

    assert match == ("Databricks Inc", DATABRICKS_PROFILE_URL)


def test_summarize_profile_classifies_strong_signal() -> None:
    result = summarize_h1bgrader_profile(
        company_query="Databricks",
        matched_company="DATABRICKS INC",
        url=DATABRICKS_PROFILE_URL,
        body_text=DATABRICKS_PROFILE_TEXT,
        html=DATABRICKS_PROFILE_HTML,
    )

    assert result.signal == "Strong signal"
    assert result.matched_company == "DATABRICKS INC"
    assert any(
        "173 certified LCA filings and 0 denials in fiscal year 2026" in item
        for item in result.evidence
    )
    assert result.profile is not None
    assert result.profile.lca_approvals[0].model_dump() == {
        "fiscal_year": 2026,
        "counts": {
            "certified": 173,
            "certified_withdrawn": 0,
            "withdrawn": 1,
            "denied": 0,
        },
    }


def test_summarize_profile_classifies_lca_table_as_strong_signal() -> None:
    result = summarize_h1bgrader_profile(
        company_query="Databricks",
        matched_company="DATABRICKS INC",
        url=DATABRICKS_PROFILE_URL,
        body_text=DATABRICKS_PROFILE_TEXT,
        html=DATABRICKS_PROFILE_HTML,
    )

    assert result.signal == "Strong signal"
    assert any(
        "173 certified LCA filings and 0 denials in fiscal year 2026" in item
        for item in result.evidence
    )


def test_parse_h1bgrader_profile_extracts_lca_tables() -> None:
    profile = parse_h1bgrader_profile(DATABRICKS_PROFILE_HTML)

    assert [row.model_dump() for row in profile.lca_approvals[:3]] == [
        {
            "fiscal_year": 2026,
            "counts": {
                "certified": 173,
                "certified_withdrawn": 0,
                "withdrawn": 1,
                "denied": 0,
            },
        },
        {
            "fiscal_year": 2025,
            "counts": {
                "certified": 376,
                "certified_withdrawn": 9,
                "withdrawn": 0,
                "denied": 0,
            },
        },
        {
            "fiscal_year": 2024,
            "counts": {
                "certified": 292,
                "certified_withdrawn": 33,
                "withdrawn": 1,
                "denied": 0,
            },
        },
    ]
    assert [row.model_dump() for row in profile.lca_approval_rates] == [
        {"fiscal_year": 2026, "approval_rate": 100.0, "denial_rate": 0.0},
        {"fiscal_year": 2025, "approval_rate": 100.0, "denial_rate": 0.0},
        {"fiscal_year": 2019, "approval_rate": 98.55, "denial_rate": 1.45},
    ]
    assert [row.model_dump() for row in profile.uscis_approvals] == [
        {
            "fiscal_year": 2026,
            "counts": {
                "new_approvals": 0,
                "continuing_approvals": 0,
                "new_denials": 0,
                "continuing_denials": 0,
            },
        },
        {
            "fiscal_year": 2025,
            "counts": {
                "new_approvals": 70,
                "continuing_approvals": 267,
                "new_denials": 0,
                "continuing_denials": 0,
            },
        },
        {
            "fiscal_year": 2024,
            "counts": {
                "new_approvals": 81,
                "continuing_approvals": 202,
                "new_denials": 0,
                "continuing_denials": 0,
            },
        },
    ]
    assert [row.model_dump() for row in profile.uscis_approval_rates] == [
        {"fiscal_year": 2026, "approval_rate": None, "denial_rate": None},
        {"fiscal_year": 2025, "approval_rate": 100.0, "denial_rate": 0.0},
        {"fiscal_year": 2023, "approval_rate": 98.04, "denial_rate": 1.96},
    ]


def test_company_profile_cache_reads_by_company_alias(tmp_path: Path) -> None:
    cache = CompanyProfileCache(cache_settings(tmp_path))
    profile = databricks_company_profile()

    cache.set(profile)

    cached_profile = cache.get("Databricks Inc")
    assert cached_profile is not None
    assert cached_profile.matched_company == "DATABRICKS INC"
    assert cached_profile.profile.lca_approvals[0].counts["certified"] == 173


def test_company_profile_cache_ignores_stale_entries(tmp_path: Path) -> None:
    settings = cache_settings(tmp_path, cache_ttl_seconds=60)
    cache = CompanyProfileCache(settings)
    stale_profile = databricks_company_profile(
        fetched_at=datetime.now(UTC) - timedelta(hours=2)
    )

    cache.set(stale_profile)

    assert cache.get("Databricks") is None


def test_service_reuses_cached_company_profile(tmp_path: Path) -> None:
    async def run_check() -> None:
        settings = cache_settings(tmp_path)
        fetcher = FakeProfileFetcher(databricks_company_profile())
        service = H1BGraderService(settings, client=fetcher)

        first_result = await service.check_company("Databricks")
        second_result = await service.check_company("Databricks Inc")

        assert fetcher.calls == ["Databricks"]
        assert first_result.signal == "Strong signal"
        assert second_result.signal == "Strong signal"
        assert second_result.matched_company == "DATABRICKS INC"

    asyncio.run(run_check())


def test_service_logs_cache_and_fetch_steps(tmp_path: Path) -> None:
    async def run_check() -> None:
        settings = cache_settings(tmp_path)
        logger = FakeLogSink()
        fetcher = FakeProfileFetcher(databricks_company_profile())
        service = H1BGraderService(settings, client=fetcher)

        await service.check_company("Databricks", logger=logger)

        messages = [message for _, message in logger.messages]
        assert fetcher.logger is logger
        assert "Checking local company-profile cache." in messages
        assert "No fresh cache entry found; starting live lookup." in messages
        assert "Caching parsed H1BGrader company profile." in messages
        assert "Building sponsorship signal from company profile." in messages

    asyncio.run(run_check())


def test_summarize_profile_classifies_no_sponsor() -> None:
    result = summarize_h1bgrader_profile(
        company_query="No Sponsor Company",
        matched_company="NO SPONSOR COMPANY INC",
        url="https://h1bgrader.com/h1b-sponsors/no-sponsor-company-inc-test",
        body_text="No Sponsor Company INC does not sponsor H1B visas.",
    )

    assert result.signal == "No sponsor"
    assert result.profile is None


def test_challenge_detection_matches_cloudflare_verification() -> None:
    assert is_challenge_page(
        title="Just a moment...",
        body_text="h1bgrader.com\nVerifying you are human. Performance and Security by Cloudflare",
        url="https://h1bgrader.com/?__cf_chl_rt_tk=abc",
    )


def test_challenge_detection_does_not_match_cloudflare_mentions_alone() -> None:
    assert not is_challenge_page(
        title="H1BGrader",
        body_text="Privacy settings mention Cloudflare but the search page is loaded.",
        url="https://h1bgrader.com/",
    )


def test_challenge_detection_does_not_match_cleared_cloudflare_url_token() -> None:
    assert not is_challenge_page(
        title="H1BGrader",
        body_text="Search H1B sponsors by company name.",
        url="https://h1bgrader.com/?__cf_chl_rt_tk=abc",
    )


def test_seleniumbase_timeout_multiplier_has_floor() -> None:
    assert seleniumbase_timeout_multiplier(10_000) == 1
    assert seleniumbase_timeout_multiplier(60_000) == 2
