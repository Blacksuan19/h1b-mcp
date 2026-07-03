import re

COMPANY_INPUT_SELECTOR = (
    "input[placeholder*='Company' i], "
    "input[placeholder*='Search' i], "
    "input[aria-label*='Company' i], "
    "input[aria-label*='Search' i], "
    "input[type='search'], "
    "input[name*='search' i], "
    "input[name*='company' i]"
)
COMPANY_PROFILE_PATH_RE = re.compile(r"/h1b-sponsors/", re.I)
COMPANY_SUGGESTION_SELECTOR = ".tt-menu.tt-open .tt-suggestion.tt-selectable"
COMPANY_SUFFIXES = {
    "co",
    "company",
    "corp",
    "corporation",
    "inc",
    "incorporated",
    "limited",
    "llc",
    "ltd",
    "plc",
}

CHALLENGE_MARKERS = (
    "attention required! | cloudflare",
    "just a moment",
    "sorry, you have been blocked",
    "verifying you are human",
    "this website uses a security service to protect against malicious bots",
    "performing security verification",
)

FISCAL_YEAR_RE = re.compile(r"\b(?:fiscal year|fy)\s*(20\d{2})\b", re.I)
GRADE_RE = re.compile(r"\b(?:grade|score)\b[:\s]+([A-F][+-]?)\b", re.I)
LCA_COUNT_RE = re.compile(r"\b(?:filed|submitted)\b.{0,80}\b(\d[\d,]*)\b.{0,80}\bLCA", re.I | re.S)
NO_SPONSOR_RE = re.compile(
    r"\b(?:does not|don't|do not|no)\b.{0,80}\bsponsor(?:s|ed|ing)?\b.{0,80}\bh-?1b\b",
    re.I | re.S,
)
YES_SPONSOR_RE = re.compile(r"\byes\b.{0,80}\bsponsor(?:s|ed|ing)?\b.{0,80}\bh-?1b\b", re.I | re.S)
