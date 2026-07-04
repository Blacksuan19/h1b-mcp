import asyncio
from contextlib import suppress
from typing import Any, TypeVar

from h1b_mcp.constants import (
    COMPANY_INPUT_SELECTOR,
    COMPANY_SUGGESTION_SELECTOR,
    SEARCH_INPUT_SELECTORS,
    SEARCH_TAB_SELECTORS,
)
from h1b_mcp.h1bgrader.browser import HomepageSession, raise_if_challenged
from h1b_mcp.h1bgrader.lookups import (
    COMPANY_LOOKUP_SPEC,
    JOB_TITLE_LOOKUP_SPEC,
    LOCATION_LOOKUP_SPEC,
    H1BGraderLookupSpec,
)
from h1b_mcp.logging import LogSink, ThreadLogBridge, log_message
from h1b_mcp.models import (
    CompanyProfile,
    H1BLookupResult,
    JobTitleProfile,
    LocationProfile,
)
from h1b_mcp.parsers.summary import build_h1b_lookup_result
from h1b_mcp.settings import Settings

TProfile = TypeVar("TProfile", CompanyProfile, JobTitleProfile, LocationProfile)


class H1BGraderClient:
    """Browser-backed client for fetching and parsing live H1BGrader company pages."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def check_company(self, company_name: str) -> H1BLookupResult:
        company_profile = await self.fetch_company_profile(company_name)
        return build_h1b_lookup_result(company_query=company_name, company_profile=company_profile)

    async def fetch_company_profile(
        self,
        company_name: str,
        *,
        logger: LogSink | None = None,
    ) -> CompanyProfile:
        """Run the SeleniumBase flow in a worker thread and return a parsed profile."""
        return await self._fetch_profile(
            company_name,
            spec=COMPANY_LOOKUP_SPEC,
            logger=logger,
        )

    async def fetch_job_title_profile(
        self,
        job_title: str,
        *,
        logger: LogSink | None = None,
    ) -> JobTitleProfile:
        """Fetch and parse the H1BGrader result page for a job title."""
        return await self._fetch_profile(
            job_title,
            spec=JOB_TITLE_LOOKUP_SPEC,
            logger=logger,
        )

    async def fetch_location_profile(
        self,
        location: str,
        *,
        logger: LogSink | None = None,
    ) -> LocationProfile:
        """Fetch and parse the H1BGrader result page for a location."""
        return await self._fetch_profile(
            location,
            spec=LOCATION_LOOKUP_SPEC,
            logger=logger,
        )

    async def _fetch_profile(
        self,
        query: str,
        *,
        spec: H1BGraderLookupSpec[TProfile],
        logger: LogSink | None,
    ) -> TProfile:
        query = query.strip()
        if not query:
            raise ValueError(f"{spec.field_name} cannot be empty")

        await log_message(logger, "info", "Launching SeleniumBase UC browser session.")
        loop = asyncio.get_running_loop()
        thread_logger = ThreadLogBridge(logger, loop)
        return await asyncio.to_thread(self._fetch_profile_sync, query, spec, thread_logger)

    def _fetch_profile_sync(
        self,
        query: str,
        spec: H1BGraderLookupSpec[TProfile],
        logger: ThreadLogBridge,
    ) -> TProfile:
        """Search H1BGrader, validate navigation, and parse the selected profile."""
        with self._homepage_session(logger) as sb:
            matched_name = self._search_and_select(
                sb,
                search_type=spec.search_type,
                query=query,
                logger=logger,
            )

            url = sb.get_current_url()
            if not spec.path_pattern.search(url):
                raise RuntimeError(
                    f"H1BGrader did not navigate to a {spec.label} profile page. "
                    f"Current URL: {url}"
                )

            self._open_profile_tabs(sb, logger, spec.tabs_to_open)

            logger.info(f"Parsing H1BGrader {spec.label} profile tables.")
            profile = spec.parse(query, matched_name, url, sb)
            logger.info(f"Finished parsing H1BGrader {spec.label} profile tables.")
            return profile

    def _homepage_session(self, logger: ThreadLogBridge) -> HomepageSession:
        """Create a SeleniumBase UC session and yield it after homepage verification."""
        return HomepageSession(self._settings, logger)

    def _search_and_select(
        self,
        sb: Any,
        *,
        search_type: str,
        query: str,
        logger: ThreadLogBridge,
    ) -> str | None:
        """Use H1BGrader's shared typeahead search flow and click the best suggestion."""
        tab_selector = SEARCH_TAB_SELECTORS[search_type]
        input_selector = SEARCH_INPUT_SELECTORS[search_type]
        label = search_type.replace("_", " ")

        if sb.is_element_visible(tab_selector):
            logger.info(f"Opening H1BGrader {label} search tab.")
            sb.click(tab_selector)
            sb.sleep(1)
            raise_if_challenged(sb)

        if not sb.is_element_visible(input_selector):
            if search_type == "company" and sb.is_element_visible(COMPANY_INPUT_SELECTOR):
                input_selector = COMPANY_INPUT_SELECTOR
            else:
                raise RuntimeError(f"H1BGrader {label} search input was not visible.")

        logger.info(f"Searching H1BGrader {label} tab for {query}.")
        sb.click(input_selector)
        with suppress(Exception):
            sb.clear(input_selector)
        sb.type(input_selector, query)
        sb.sleep(2)
        raise_if_challenged(sb)

        if not sb.is_element_visible(COMPANY_SUGGESTION_SELECTOR):
            raise RuntimeError(f"H1BGrader returned no selectable {label} result for {query}.")

        matched_query = sb.get_text(COMPANY_SUGGESTION_SELECTOR).strip() or None
        logger.info(f"Selecting H1BGrader result: {matched_query or 'unknown result'}.")
        sb.click(COMPANY_SUGGESTION_SELECTOR)
        sb.sleep(6)
        raise_if_challenged(sb)
        return matched_query

    def _open_profile_tabs(
        self,
        sb: Any,
        logger: ThreadLogBridge,
        tabs: tuple[tuple[str, str], ...],
    ) -> None:
        """Load tabs whose table data is rendered after tab activation."""
        for selector, label in tabs:
            self._open_optional_tab(sb, selector=selector, label=label, logger=logger)

    def _open_optional_tab(
        self,
        sb: Any,
        *,
        selector: str,
        label: str,
        logger: ThreadLogBridge,
    ) -> None:
        """Open a tab when present and continue with partial HTML when absent."""
        if not sb.is_element_visible(selector):
            logger.warning(
                f"H1BGrader {label} tab was not visible; parsing current profile HTML."
            )
            return

        logger.info(f"Opening H1B {label} tab.")
        sb.click(selector)
        sb.sleep(2)
        raise_if_challenged(sb)
