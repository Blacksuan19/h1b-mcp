import re
from collections.abc import Iterable

from h1b_mcp.constants import CHALLENGE_MARKERS, COMPANY_SUFFIXES


def normalize_company_name(value: str) -> str:
    """Normalize names for fuzzy matching while ignoring common legal suffixes."""
    cleaned = re.sub(r"[^a-z0-9]+", " ", value.lower())
    parts = [part for part in cleaned.split() if part not in COMPANY_SUFFIXES]
    return " ".join(parts)


def best_company_match(query: str, candidates: Iterable[tuple[str, str]]) -> tuple[str, str] | None:
    """Pick the most plausible search result when only candidate text and URLs are available.

    H1BGrader names often include capitalization, punctuation, and legal suffixes that do not
    appear in the user's query. The scorer favors exact normalized matches, then substring
    containment, then token overlap.
    """
    normalized_query = normalize_company_name(query)
    scored: list[tuple[int, str, str]] = []

    for name, href in candidates:
        normalized_name = normalize_company_name(name)
        if not normalized_name:
            continue
        if normalized_name == normalized_query:
            score = 100
        elif normalized_query in normalized_name or normalized_name in normalized_query:
            score = 80
        else:
            query_parts = set(normalized_query.split())
            name_parts = set(normalized_name.split())
            score = len(query_parts & name_parts) * 10
        scored.append((score, name.strip(), href))

    scored.sort(reverse=True)
    if scored and scored[0][0] > 0:
        _, name, href = scored[0]
        return name, href
    return None


def is_challenge_page(*, title: str, body_text: str, url: str) -> bool:
    """Detect Cloudflare or verification pages from the browser title, body, or URL."""
    challenge_text = f"{title}\n{body_text}\n{url}".lower()
    return any(marker in challenge_text for marker in CHALLENGE_MARKERS)


def seleniumbase_timeout_multiplier(timeout_ms: int) -> float:
    """Map the app timeout setting to SeleniumBase's 30-second multiplier convention."""
    return max(timeout_ms / 30_000, 1)
