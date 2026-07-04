from collections.abc import Awaitable, Callable
from typing import Protocol, TypeVar

from h1b_mcp.cache import (
    ProfileCache,
    profile_aliases,
)
from h1b_mcp.h1bgrader import H1BGraderClient
from h1b_mcp.logging import LogSink, log_message
from h1b_mcp.models import CompanyProfile, JobTitleProfile, LocationProfile
from h1b_mcp.settings import Settings

TProfile = TypeVar("TProfile", CompanyProfile, JobTitleProfile, LocationProfile)


class H1BGraderProfileFetcher(Protocol):
    """Small client protocol that lets tests swap out the live browser fetcher."""

    async def fetch_company_profile(
        self,
        company_name: str,
        *,
        logger: LogSink | None = None,
    ) -> CompanyProfile:
        ...

    async def fetch_job_title_profile(
        self,
        job_title: str,
        *,
        logger: LogSink | None = None,
    ) -> JobTitleProfile:
        ...

    async def fetch_location_profile(
        self,
        location: str,
        *,
        logger: LogSink | None = None,
    ) -> LocationProfile:
        ...


class H1BGraderService:
    """Coordinates cache reuse, live H1BGrader fetches, and profile-level responses."""

    def __init__(
        self,
        settings: Settings,
        *,
        client: H1BGraderProfileFetcher | None = None,
        company_cache: ProfileCache[CompanyProfile] | None = None,
        job_title_cache: ProfileCache[JobTitleProfile] | None = None,
        location_cache: ProfileCache[LocationProfile] | None = None,
    ) -> None:
        self._client = client or H1BGraderClient(settings)
        self._company_cache = company_cache or ProfileCache(
            cache_dir=settings.cache_dir,
            ttl_seconds=settings.cache_ttl_seconds,
            model_type=CompanyProfile,
            aliases=profile_aliases,
        )
        self._job_title_cache = job_title_cache or ProfileCache(
            cache_dir=settings.job_title_cache_dir,
            ttl_seconds=settings.cache_ttl_seconds,
            model_type=JobTitleProfile,
            aliases=profile_aliases,
        )
        self._location_cache = location_cache or ProfileCache(
            cache_dir=settings.location_cache_dir,
            ttl_seconds=settings.cache_ttl_seconds,
            model_type=LocationProfile,
            aliases=profile_aliases,
        )

    async def get_company_profile(
        self,
        company_name: str,
        *,
        force_refresh: bool = False,
        logger: LogSink | None = None,
    ) -> CompanyProfile:
        """Return a fresh cached profile or fetch, parse, and cache a live H1BGrader page."""
        company_name = company_name.strip()
        if not company_name:
            raise ValueError("company_name cannot be empty")

        return await self._get_profile(
            query=company_name,
            cache=self._company_cache,
            fetch=lambda: self._client.fetch_company_profile(company_name, logger=logger),
            profile_label="company",
            cached_name=lambda profile: profile.matched_name,
            force_refresh=force_refresh,
            logger=logger,
        )

    async def get_job_title_profile(
        self,
        job_title: str,
        *,
        force_refresh: bool = False,
        logger: LogSink | None = None,
    ) -> JobTitleProfile:
        """Return a fresh cached job-title profile or fetch, parse, and cache one."""
        job_title = job_title.strip()
        if not job_title:
            raise ValueError("job_title cannot be empty")

        return await self._get_profile(
            query=job_title,
            cache=self._job_title_cache,
            fetch=lambda: self._client.fetch_job_title_profile(job_title, logger=logger),
            profile_label="job-title",
            cached_name=lambda profile: profile.matched_name,
            force_refresh=force_refresh,
            logger=logger,
        )

    async def get_location_profile(
        self,
        location: str,
        *,
        force_refresh: bool = False,
        logger: LogSink | None = None,
    ) -> LocationProfile:
        """Return a fresh cached location profile or fetch, parse, and cache one."""
        location = location.strip()
        if not location:
            raise ValueError("location cannot be empty")

        return await self._get_profile(
            query=location,
            cache=self._location_cache,
            fetch=lambda: self._client.fetch_location_profile(location, logger=logger),
            profile_label="location",
            cached_name=lambda profile: profile.matched_name,
            force_refresh=force_refresh,
            logger=logger,
        )

    async def _get_profile(
        self,
        *,
        query: str,
        cache: ProfileCache[TProfile],
        fetch: Callable[[], Awaitable[TProfile]],
        profile_label: str,
        cached_name: Callable[[TProfile], str | None],
        force_refresh: bool,
        logger: LogSink | None,
    ) -> TProfile:
        """Shared cache/fetch/write path for all H1BGrader profile types."""
        if not force_refresh:
            await log_message(logger, "info", f"Checking local {profile_label} profile cache.")
            cached_profile = cache.get(query)
            if cached_profile:
                name = cached_name(cached_profile) or query
                await log_message(
                    logger,
                    "info",
                    f"Using cached H1BGrader {profile_label} profile for {name}.",
                )
                return cached_profile
            await log_message(logger, "info", "No fresh cache entry found; starting live lookup.")
        else:
            await log_message(logger, "info", "Force refresh requested; skipping cache read.")

        await log_message(logger, "info", f"Fetching H1BGrader {profile_label} profile: {query}.")
        profile = await fetch()
        await log_message(logger, "info", f"Caching parsed H1BGrader {profile_label} profile.")
        cache.set(profile)
        return profile
