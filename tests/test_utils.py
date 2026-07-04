from h1b_mcp.utils import (
    best_company_match,
    is_challenge_page,
    normalize_company_name,
    seleniumbase_timeout_multiplier,
)
from tests.fixtures import DATABRICKS_PROFILE_URL


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
