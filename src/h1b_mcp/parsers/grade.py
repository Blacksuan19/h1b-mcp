import re
from typing import Any

from bs4 import BeautifulSoup

from h1b_mcp.models import AnnualGradeRow, GradeInsight, GradeProfile


def parse_grade_profile(html: str) -> GradeProfile | None:
    if not html.strip():
        return None

    soup = BeautifulSoup(html, "html.parser")
    section = soup.select_one("#employer-grade")
    if section is None:
        return None

    annual_grades = parse_annual_grades(section)
    insights = parse_grade_insights(section)
    confidence = parse_confidence(section)

    if not annual_grades and not insights and not confidence:
        return None

    return GradeProfile(
        latest_grade=latest_grade(annual_grades),
        confidence=confidence,
        annual_grades=annual_grades,
        insights=insights,
    )


def parse_annual_grades(section: Any) -> list[AnnualGradeRow]:
    rows: list[AnnualGradeRow] = []
    for card in section.select("div.border.rounded"):
        text = compact_text(card)
        match = re.search(
            r"\b(20\d{2})\s+Grade\s+([A-F][+-]?)\b(?:\s+(.+?Sep\s+20\d{2}))?",
            text,
            re.I,
        )
        if not match:
            continue
        rows.append(
            AnnualGradeRow(
                fiscal_year=int(match.group(1)),
                grade=match.group(2).upper(),
                period=match.group(3),
            )
        )
    rows.sort(key=lambda row: row.fiscal_year, reverse=True)
    return rows


def parse_confidence(section: Any) -> str | None:
    confidence = section.select_one(".confidence")
    if confidence is None:
        return None
    value = compact_text(confidence)
    return value or None


def parse_grade_insights(section: Any) -> list[GradeInsight]:
    insights: list[GradeInsight] = []
    for callout in section.select(".bs-callout"):
        title_element = callout.find(["h1", "h2", "h3", "h4", "h5", "h6"])
        if title_element is None:
            continue
        title = compact_text(title_element)
        body = compact_text(callout)
        description = body.removeprefix(title).strip()
        status = parse_badge_status(callout)
        score, score_max = parse_score(description)
        insights.append(
            GradeInsight(
                title=title,
                description=description,
                score=score,
                score_max=score_max,
                status=status,
                sentiment=parse_sentiment(callout),
            )
        )
    return insights


def parse_badge_status(callout: Any) -> str | None:
    for badge in callout.select(".badge"):
        value = compact_text(badge)
        if value and not re.fullmatch(r"\d{1,3}\s*/\s*\d{1,3}", value):
            return value
    return None


def parse_score(value: str) -> tuple[int | None, int | None]:
    match = re.search(r"\b(\d{1,3})\s*/\s*(\d{1,3})\b", value)
    if not match:
        return None, None
    return int(match.group(1)), int(match.group(2))


def parse_sentiment(callout: Any) -> str | None:
    classes = set(callout.get("class") or [])
    if "bs-callout-success" in classes:
        return "positive"
    if "bs-callout-warning" in classes:
        return "warning"
    if "bs-callout-danger" in classes:
        return "negative"
    return None


def latest_grade(rows: list[AnnualGradeRow]) -> str | None:
    return rows[0].grade if rows else None


def compact_text(value: Any) -> str:
    return re.sub(r"\s+", " ", value.get_text(" ", strip=True)).strip()
