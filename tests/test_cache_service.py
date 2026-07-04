import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path

from h1b_mcp.cache import (
    ProfileCache,
    profile_aliases,
)
from h1b_mcp.models import CompanyProfile, JobTitleProfile, LocationProfile
from h1b_mcp.service import H1BGraderService
from tests.fixtures import (
    FakeLogSink,
    FakeProfileFetcher,
    cache_settings,
    chicago_location_profile,
    databricks_company_profile,
    machine_learning_engineer_profile,
)


def test_company_profile_cache_reads_by_company_alias(tmp_path: Path) -> None:
    settings = cache_settings(tmp_path)
    cache = ProfileCache(
        cache_dir=settings.cache_dir,
        ttl_seconds=settings.cache_ttl_seconds,
        model_type=CompanyProfile,
        aliases=profile_aliases,
    )
    profile = databricks_company_profile()

    cache.set(profile)

    cached_profile = cache.get("Databricks Inc")
    assert cached_profile is not None
    assert cached_profile.matched_name == "DATABRICKS INC"
    assert cached_profile.profile.lca_approvals[0].counts["certified"] == 173
    cached_json = cached_profile.model_dump(mode="json")
    assert "sponsor_status" not in cached_json
    assert "reported_lca_count" not in cached_json
    assert "reported_lca_fiscal_year" not in cached_json
    assert "grade" not in cached_json


def test_company_profile_cache_ignores_stale_entries(tmp_path: Path) -> None:
    settings = cache_settings(tmp_path, cache_ttl_seconds=60)
    cache = ProfileCache(
        cache_dir=settings.cache_dir,
        ttl_seconds=settings.cache_ttl_seconds,
        model_type=CompanyProfile,
        aliases=profile_aliases,
    )
    stale_profile = databricks_company_profile(
        fetched_at=datetime.now(UTC) - timedelta(hours=2)
    )

    cache.set(stale_profile)

    assert cache.get("Databricks") is None


def test_job_title_profile_cache_reads_by_alias(tmp_path: Path) -> None:
    settings = cache_settings(tmp_path)
    cache = ProfileCache(
        cache_dir=settings.job_title_cache_dir,
        ttl_seconds=settings.cache_ttl_seconds,
        model_type=JobTitleProfile,
        aliases=profile_aliases,
    )
    profile = machine_learning_engineer_profile()

    cache.set(profile)

    cached_profile = cache.get("machine learning engineer")
    assert cached_profile is not None
    assert cached_profile.matched_name == "MACHINE LEARNING ENGINEER"
    assert cached_profile.profile.employers[0].employer_name == "Adobe INC"


def test_location_profile_cache_reads_by_alias(tmp_path: Path) -> None:
    settings = cache_settings(tmp_path)
    cache = ProfileCache(
        cache_dir=settings.location_cache_dir,
        ttl_seconds=settings.cache_ttl_seconds,
        model_type=LocationProfile,
        aliases=profile_aliases,
    )
    profile = chicago_location_profile()

    cache.set(profile)

    cached_profile = cache.get("Chicago")
    assert cached_profile is not None
    assert cached_profile.matched_name == "CHICAGO, IL"
    assert cached_profile.profile.employers[0].lca_count == 126


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


def test_service_reuses_cached_job_title_profile(tmp_path: Path) -> None:
    async def run_check() -> None:
        settings = cache_settings(tmp_path)
        fetcher = FakeProfileFetcher(
            databricks_company_profile(),
            job_title_profile=machine_learning_engineer_profile(),
        )
        service = H1BGraderService(settings, client=fetcher)

        first_result = await service.get_job_title_profile("Machine Learning Engineer")
        second_result = await service.get_job_title_profile("MACHINE LEARNING ENGINEER")

        assert fetcher.job_title_calls == ["Machine Learning Engineer"]
        assert first_result.matched_name == "MACHINE LEARNING ENGINEER"
        assert second_result.profile.employers[0].employer_name == "Adobe INC"

    asyncio.run(run_check())


def test_service_reuses_cached_location_profile(tmp_path: Path) -> None:
    async def run_check() -> None:
        settings = cache_settings(tmp_path)
        fetcher = FakeProfileFetcher(
            databricks_company_profile(),
            location_profile=chicago_location_profile(),
        )
        service = H1BGraderService(settings, client=fetcher)

        first_result = await service.get_location_profile("Chicago")
        second_result = await service.get_location_profile("CHICAGO, IL")

        assert fetcher.location_calls == ["Chicago"]
        assert first_result.matched_name == "CHICAGO, IL"
        assert second_result.profile.h1b_salaries[0].average_salary == 190500

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
        assert "Checking local company profile cache." in messages
        assert "No fresh cache entry found; starting live lookup." in messages
        assert "Caching parsed H1BGrader company profile." in messages
        assert "Building sponsorship signal from company profile." in messages

    asyncio.run(run_check())
