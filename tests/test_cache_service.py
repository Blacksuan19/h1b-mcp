import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path

from h1b_mcp.cache import CompanyProfileCache
from h1b_mcp.service import H1BGraderService
from tests.fixtures import (
    FakeLogSink,
    FakeProfileFetcher,
    cache_settings,
    databricks_company_profile,
)


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
