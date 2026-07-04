import re
from typing import Literal

from h1b_mcp.models import JobTitleMatch, JobTitleRow

JobTitleMatchType = Literal["exact", "close", "adjacent"]

TITLE_SYNONYMS = {
    "architect": {"solution", "solutions", "architect"},
    "data": {"data", "analytics", "analyst", "scientist"},
    "engineer": {"engineer", "engineering", "developer", "software", "technical"},
    "machine": {"machine", "ml", "ai", "data", "scientist", "software", "engineer"},
    "manager": {"manager", "management", "lead", "director", "product", "program"},
    "ml": {"machine", "learning", "ml", "ai", "data", "scientist", "software", "engineer"},
    "product": {"product", "manager", "operations", "strategy"},
    "sales": {"sales", "solutions", "solution", "architect", "consultant"},
    "scientist": {"scientist", "data", "analytics", "machine", "learning", "ml", "ai"},
    "software": {"software", "engineer", "developer", "technical", "engineering"},
    "solution": {"solution", "solutions", "architect", "consultant", "engineer"},
    "solutions": {"solution", "solutions", "architect", "consultant", "engineer"},
    "technical": {"technical", "engineer", "solutions", "support", "staff"},
}

TITLE_STOPWORDS = {
    "and",
    "i",
    "ii",
    "iii",
    "iv",
    "of",
    "the",
}


def match_job_titles(
    query: str,
    job_titles: list[JobTitleRow],
    *,
    limit: int = 5,
) -> list[JobTitleMatch]:
    """Return the strongest sponsored-title matches for a free-form role query.

    The matcher is intentionally local and explainable: it only uses the parsed company title
    table, then ranks exact title evidence above close token matches and adjacent synonym matches.
    """
    query_tokens = title_tokens(query)
    if not query_tokens:
        return []

    matches: list[JobTitleMatch] = []
    for job_title in job_titles:
        match_type, score = score_title_match(query_tokens, title_tokens(job_title.title))
        if match_type is None:
            continue
        matches.append(
            JobTitleMatch(
                title=job_title.title,
                match_type=match_type,
                score=round(score, 3),
                lca_count=job_title.lca_count,
                maximum_salary=job_title.maximum_salary,
                average_salary=job_title.average_salary,
                minimum_salary=job_title.minimum_salary,
            )
        )

    matches.sort(
        key=lambda match: (
            match_score_rank(match.match_type),
            match.score,
            match.lca_count,
        ),
        reverse=True,
    )
    return matches[:limit]


def score_title_match(
    query_tokens: set[str],
    title_tokens_value: set[str],
) -> tuple[JobTitleMatchType | None, float]:
    """Classify title evidence without pretending adjacent roles are exact matches."""
    if query_tokens == title_tokens_value:
        return "exact", 1.0

    overlap = len(query_tokens & title_tokens_value)
    overlap_score = overlap / max(len(query_tokens), 1)
    if overlap_score == 1:
        return "close", 1.0
    if overlap_score >= 0.6:
        return "close", overlap_score

    expanded_query = expand_tokens(query_tokens)
    expanded_title = expand_tokens(title_tokens_value)
    adjacent_overlap = len(expanded_query & expanded_title)
    adjacent_score = adjacent_overlap / max(len(query_tokens | title_tokens_value), 1)
    if adjacent_score >= 0.45:
        return "adjacent", adjacent_score

    return None, 0.0


def title_tokens(value: str) -> set[str]:
    """Tokenize titles for matching while folding common seniority abbreviations."""
    tokens = {
        token
        for token in re.findall(r"[a-z0-9]+", value.lower().replace("&", " and "))
        if token not in TITLE_STOPWORDS
    }
    if "sr" in tokens:
        tokens.remove("sr")
        tokens.add("senior")
    return tokens


def expand_tokens(tokens: set[str]) -> set[str]:
    """Add small hand-curated synonym groups for adjacent job-title evidence."""
    expanded = set(tokens)
    for token in tokens:
        expanded.update(TITLE_SYNONYMS.get(token, set()))
    return expanded


def match_score_rank(match_type: str) -> int:
    """Keep match sorting aligned with the public job sponsorship signal hierarchy."""
    return {"exact": 3, "close": 2, "adjacent": 1}.get(match_type, 0)
