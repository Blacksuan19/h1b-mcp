from typing import Protocol

from h1b_mcp.cache import CompanyProfileCache
from h1b_mcp.h1bgrader import H1BGraderClient
from h1b_mcp.logging import LogSink, log_message
from h1b_mcp.models import CompanyProfile, H1BLookupResult
from h1b_mcp.parsers.summary import build_h1b_lookup_result
from h1b_mcp.settings import Settings


class CompanyProfileFetcher(Protocol):
    async def fetch_company_profile(
        self,
        company_name: str,
        *,
        logger: LogSink | None = None,
    ) -> CompanyProfile:
        ...


class H1BGraderService:
    def __init__(
        self,
        settings: Settings,
        *,
        client: CompanyProfileFetcher | None = None,
        cache: CompanyProfileCache | None = None,
    ) -> None:
        self._client = client or H1BGraderClient(settings)
        self._cache = cache or CompanyProfileCache(settings)

    async def check_company(
        self,
        company_name: str,
        *,
        force_refresh: bool = False,
        logger: LogSink | None = None,
    ) -> H1BLookupResult:
        await log_message(logger, "info", f"Checking H-1B sponsorship for {company_name}.")
        company_profile = await self.get_company_profile(
            company_name,
            force_refresh=force_refresh,
            logger=logger,
        )
        await log_message(logger, "info", "Building sponsorship signal from company profile.")
        return build_h1b_lookup_result(
            company_query=company_name,
            company_profile=company_profile,
        )

    async def get_company_profile(
        self,
        company_name: str,
        *,
        force_refresh: bool = False,
        logger: LogSink | None = None,
    ) -> CompanyProfile:
        company_name = company_name.strip()
        if not company_name:
            raise ValueError("company_name cannot be empty")

        if not force_refresh:
            await log_message(logger, "info", "Checking local company-profile cache.")
            cached_profile = self._cache.get(company_name)
            if cached_profile:
                await log_message(
                    logger,
                    "info",
                    f"Using cached H1BGrader profile for {cached_profile.matched_company}.",
                )
                return cached_profile
            await log_message(logger, "info", "No fresh cache entry found; starting live lookup.")
        else:
            await log_message(logger, "info", "Force refresh requested; skipping cache read.")

        company_profile = await self._client.fetch_company_profile(company_name, logger=logger)
        await log_message(logger, "info", "Caching parsed H1BGrader company profile.")
        self._cache.set(company_profile)
        return company_profile
