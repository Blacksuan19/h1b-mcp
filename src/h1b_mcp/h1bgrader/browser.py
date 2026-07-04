import sys
from types import TracebackType
from typing import Any

from seleniumbase import SB  # type: ignore[reportMissingTypeStubs]

from h1b_mcp.logging import ThreadLogBridge
from h1b_mcp.models import H1BGraderBlockedError
from h1b_mcp.settings import Settings
from h1b_mcp.utils import is_challenge_page, seleniumbase_timeout_multiplier


class HomepageSession:
    """Own the SeleniumBase session lifecycle and homepage readiness check."""

    def __init__(
        self,
        settings: Settings,
        logger: ThreadLogBridge,
    ) -> None:
        self._settings = settings
        self._logger = logger
        self._sb_context: Any | None = None

    def __enter__(self) -> Any:
        self._settings.profile_dir.mkdir(parents=True, exist_ok=True)
        self._sb_context = SB(
            browser="chrome",
            uc=True,
            headless=True,
            user_data_dir=str(self._settings.profile_dir),
            timeout_multiplier=seleniumbase_timeout_multiplier(self._settings.timeout_ms),
        )
        sb = self._sb_context.__enter__()
        try:
            self._open_homepage(sb)
        except BaseException:
            self._sb_context.__exit__(*sys.exc_info())
            raise
        return sb

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        if self._sb_context is None:
            return None
        return self._sb_context.__exit__(exc_type, exc_value, traceback)

    def _open_homepage(self, sb: Any) -> None:
        """Load the shared H1BGrader search page before selecting a search tab."""
        self._logger.info("Opening H1BGrader homepage.")
        sb.uc_open_with_reconnect(self._settings.base_url, reconnect_time=6)
        sb.sleep(2)
        raise_if_challenged(sb)
        self._logger.info("H1BGrader homepage loaded.")


def raise_if_challenged(sb: Any) -> None:
    """Fail fast on Cloudflare/verification pages instead of parsing block text."""
    title = sb.get_title()
    body_text = get_body_text(sb)
    url = sb.get_current_url()
    if is_challenge_page(title=title, body_text=body_text, url=url):
        raise H1BGraderBlockedError(
            "H1BGrader presented a Cloudflare challenge or block page.",
            url=url,
        )


def get_body_text(sb: Any) -> str:
    try:
        return str(sb.get_text("body"))
    except Exception:
        return ""


def get_page_source(sb: Any) -> str:
    try:
        return str(sb.driver.page_source)
    except Exception:
        return ""
