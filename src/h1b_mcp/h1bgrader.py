import asyncio
from typing import Any

from seleniumbase import SB  # type: ignore[reportMissingTypeStubs]

from h1b_mcp.constants import (
    COMPANY_INPUT_SELECTOR,
    COMPANY_PROFILE_PATH_RE,
    COMPANY_SUGGESTION_SELECTOR,
)
from h1b_mcp.models import H1BGraderBlockedError, H1BLookupResult
from h1b_mcp.parsers.summary import summarize_h1bgrader_profile
from h1b_mcp.settings import Settings
from h1b_mcp.utils import is_challenge_page, seleniumbase_timeout_multiplier


class H1BGraderClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def check_company(self, company_name: str) -> H1BLookupResult:
        company_name = company_name.strip()
        if not company_name:
            raise ValueError("company_name cannot be empty")

        return await asyncio.to_thread(self._check_company_sync, company_name)

    def _check_company_sync(self, company_name: str) -> H1BLookupResult:
        self._settings.profile_dir.mkdir(parents=True, exist_ok=True)
        with SB(
            browser="chrome",
            uc=True,
            headless=True,
            user_data_dir=str(self._settings.profile_dir),
            timeout_multiplier=seleniumbase_timeout_multiplier(self._settings.timeout_ms),
        ) as sb:
            sb.uc_open_with_reconnect(self._settings.base_url, reconnect_time=6)
            sb.sleep(2)
            self._raise_if_challenged(sb)

            if not sb.is_element_visible(COMPANY_INPUT_SELECTOR):
                raise RuntimeError("H1BGrader company search input was not visible.")

            sb.click(COMPANY_INPUT_SELECTOR)
            sb.type(COMPANY_INPUT_SELECTOR, company_name)
            sb.sleep(2)
            self._raise_if_challenged(sb)

            if not sb.is_element_visible(COMPANY_SUGGESTION_SELECTOR):
                raise RuntimeError(
                    f"H1BGrader returned no selectable company result for {company_name}."
                )

            matched_company = sb.get_text(COMPANY_SUGGESTION_SELECTOR).strip() or None
            sb.click(COMPANY_SUGGESTION_SELECTOR)
            sb.sleep(6)
            self._raise_if_challenged(sb)

            url = sb.get_current_url()
            if not COMPANY_PROFILE_PATH_RE.search(url):
                raise RuntimeError(
                    f"H1BGrader did not navigate to a company profile. Current URL: {url}"
                )

            return summarize_h1bgrader_profile(
                company_query=company_name,
                matched_company=matched_company,
                url=url,
                body_text=self._body_text(sb),
                html=self._page_source(sb),
            )

    def _raise_if_challenged(self, sb: Any) -> None:
        title = sb.get_title()
        body_text = self._body_text(sb)
        url = sb.get_current_url()
        if is_challenge_page(title=title, body_text=body_text, url=url):
            raise H1BGraderBlockedError(
                "H1BGrader presented a Cloudflare challenge or block page.",
                url=url,
            )

    @staticmethod
    def _body_text(sb: Any) -> str:
        try:
            return str(sb.get_text("body"))
        except Exception:
            return ""

    @staticmethod
    def _page_source(sb: Any) -> str:
        try:
            return str(sb.driver.page_source)
        except Exception:
            return ""
