import re
from typing import Any

from bs4 import BeautifulSoup

from h1b_mcp.models import (
    AnnualCountRow,
    AnnualRateRow,
    AnnualSalaryRow,
    H1BGraderProfile,
    JobTitleRow,
)
from h1b_mcp.parsers.grade import parse_grade_profile

LCA_COUNT_COLUMNS = ("certified", "certified_withdrawn", "withdrawn", "denied")
USCIS_COUNT_COLUMNS = (
    "new_approvals",
    "continuing_approvals",
    "new_denials",
    "continuing_denials",
)


def parse_h1bgrader_profile(page_source: str) -> H1BGraderProfile:
    if "<table" in page_source.lower():
        return parse_h1bgrader_profile_html(page_source)

    return H1BGraderProfile(
        lca_approvals=parse_lca_approvals(page_source),
        lca_approval_rates=parse_lca_approval_rates(page_source),
        uscis_approvals=parse_uscis_approvals(page_source),
        uscis_approval_rates=parse_uscis_approval_rates(page_source),
        h1b_salaries=parse_h1b_salaries(page_source),
        job_titles=parse_job_titles(page_source),
        grade=parse_grade_profile(page_source),
    )


def parse_h1bgrader_profile_html(html: str) -> H1BGraderProfile:
    tables = extract_html_tables(html)
    return H1BGraderProfile(
        lca_approvals=parse_count_table(
            find_table(tables, "H1B LCA Approvals, Denials"),
            LCA_COUNT_COLUMNS,
        ),
        lca_approval_rates=parse_rate_table(find_table(tables, "H1B LCA Approval & Denial Rates")),
        uscis_approvals=parse_count_table(
            find_table(tables, "USCIS H1B Approvals, Denials"),
            USCIS_COUNT_COLUMNS,
        ),
        uscis_approval_rates=parse_rate_table(
            find_table(tables, "USCIS H1B Approval & Denial Rates")
        ),
        h1b_salaries=parse_salary_table(find_table(tables, "H1B Salaries")),
        job_titles=parse_job_title_table(
            find_table_with_headers(
                tables,
                (
                    "H1B Job Title",
                    "LCA Count",
                    "Maximum Salary",
                    "Average Salary",
                    "Minimum Salary",
                ),
            )
        ),
        grade=parse_grade_profile(html),
    )


def extract_html_tables(html: str) -> list[list[list[str]]]:
    soup = BeautifulSoup(html, "html.parser")
    tables: list[list[list[str]]] = []
    for table in soup.find_all("table"):
        rows: list[list[str]] = []
        caption = table.find("caption")
        if caption:
            rows.append([cell_text(caption)])
        for row in table.find_all("tr"):
            cells = [cell_text(cell) for cell in row.find_all(["th", "td"])]
            if cells:
                rows.append(cells)
        if rows:
            tables.append(rows)
    return tables


def cell_text(value: Any) -> str:
    return re.sub(r"\s+", " ", value.get_text(" ", strip=True)).strip()


def find_table(tables: list[list[list[str]]], title: str) -> list[list[str]]:
    normalized_title = normalize_header(title)
    for table in tables:
        table_text = " ".join(" ".join(row) for row in table)
        if normalized_title in normalize_header(table_text):
            return table
    return []


def find_table_with_headers(
    tables: list[list[list[str]]],
    headers: tuple[str, ...],
) -> list[list[str]]:
    normalized_headers = {normalize_header(header) for header in headers}
    for table in tables:
        for row in table:
            normalized_row = {normalize_header(cell) for cell in row}
            if normalized_headers.issubset(normalized_row):
                return table
    return []


def normalize_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def data_rows(table: list[list[str]]) -> list[list[str]]:
    return [row for row in table if row and re.fullmatch(r"20\d{2}", row[0])]


def parse_count_table(table: list[list[str]], column_keys: tuple[str, ...]) -> list[AnnualCountRow]:
    rows: list[AnnualCountRow] = []
    for row in data_rows(table):
        if len(row) < len(column_keys) + 1:
            continue
        rows.append(
            AnnualCountRow(
                fiscal_year=int(row[0]),
                counts={
                    key: parse_int_cell(row[index + 1])
                    for index, key in enumerate(column_keys)
                },
            )
        )
    return rows


def parse_count_table_from_text(
    body_text: str,
    *,
    start_marker: str,
    end_markers: tuple[str, ...],
    column_keys: tuple[str, ...],
) -> list[AnnualCountRow]:
    section = table_section(
        body_text,
        start_marker=start_marker,
        end_markers=end_markers,
    )
    rows: list[AnnualCountRow] = []
    tokens = re.findall(r"20\d{2}|[\d,]+|-", section)
    idx = 0
    while idx < len(tokens):
        if not re.fullmatch(r"20\d{2}", tokens[idx]):
            idx += 1
            continue
        if idx + len(column_keys) >= len(tokens):
            break
        rows.append(
            AnnualCountRow(
                fiscal_year=int(tokens[idx]),
                counts={
                    key: parse_int_cell(tokens[idx + index + 1])
                    for index, key in enumerate(column_keys)
                },
            )
        )
        idx += len(column_keys) + 1
    return rows


def parse_rate_table(table: list[list[str]]) -> list[AnnualRateRow]:
    rows: list[AnnualRateRow] = []
    for row in data_rows(table):
        if len(row) < 3:
            continue
        rows.append(
            AnnualRateRow(
                fiscal_year=int(row[0]),
                approval_rate=parse_percent_cell(row[1]),
                denial_rate=parse_percent_cell(row[2]),
            )
        )
    return rows


def parse_salary_table(table: list[list[str]]) -> list[AnnualSalaryRow]:
    rows: list[AnnualSalaryRow] = []
    for row in data_rows(table):
        if len(row) < 5:
            continue
        rows.append(
            AnnualSalaryRow(
                fiscal_year=int(row[0]),
                maximum_salary=parse_money_cell(row[1]),
                median_salary=parse_money_cell(row[2]),
                average_salary=parse_money_cell(row[3]),
                minimum_salary=parse_money_cell(row[4]),
            )
        )
    return rows


def parse_job_title_table(table: list[list[str]]) -> list[JobTitleRow]:
    rows: list[JobTitleRow] = []
    for row in table:
        if len(row) < 5 or not row[0] or not re.fullmatch(r"[\d,]+", row[1]):
            continue
        rows.append(
            JobTitleRow(
                title=row[0],
                lca_count=parse_int_cell(row[1]),
                maximum_salary=parse_money_cell(row[2]),
                average_salary=parse_money_cell(row[3]),
                minimum_salary=parse_money_cell(row[4]),
            )
        )
    return rows


def parse_lca_approvals(body_text: str) -> list[AnnualCountRow]:
    return parse_count_table_from_text(
        body_text,
        start_marker="H1B LCA Approvals, Denials Fiscal Year*",
        end_markers=(
            "H1B LCA Approval & Denial Rates",
            "*Fiscal Year for US Dept of Labor",
            "USCIS H1B Approvals",
        ),
        column_keys=LCA_COUNT_COLUMNS,
    )


def parse_lca_approval_rates(body_text: str) -> list[AnnualRateRow]:
    return parse_rate_table_from_text(
        body_text,
        start_marker="H1B LCA Approval & Denial Rates Fiscal Year* Approval (%) Denial (%)",
        end_markers=(
            "*Fiscal Year for US Dept of Labor",
            "USCIS H1B Approvals",
            "USCIS H1B Approval & Denial Rates",
        ),
    )


def parse_uscis_approvals(body_text: str) -> list[AnnualCountRow]:
    return parse_count_table_from_text(
        body_text,
        start_marker="USCIS H1B Approvals, Denials Fiscal Year*",
        end_markers=(
            "USCIS H1B Approval & Denial Rates",
            "H1B Job Titles",
            "Latest H1B Job Titles",
        ),
        column_keys=USCIS_COUNT_COLUMNS,
    )


def parse_uscis_approval_rates(body_text: str) -> list[AnnualRateRow]:
    return parse_rate_table_from_text(
        body_text,
        start_marker="USCIS H1B Approval & Denial Rates Fiscal Year* Approval (%) Denial (%)",
        end_markers=("H1B Job Titles", "Latest H1B Job Titles"),
    )


def parse_h1b_salaries(body_text: str) -> list[AnnualSalaryRow]:
    section = table_section(
        body_text,
        start_marker="H1B Salaries Fiscal Year* Maximum Median Average Minimum",
        end_markers=(
            "*Fiscal Year for US Dept of Labor",
            "View Latest H1B Salaries",
            "H1B Job Title",
        ),
    )
    rows: list[AnnualSalaryRow] = []
    for match in re.finditer(
        r"\b(20\d{2})\s+(\$[\d,]+|-|N/A)\s+(\$[\d,]+|-|N/A)\s+"
        r"(\$[\d,]+|-|N/A)\s+(\$[\d,]+|-|N/A)",
        section,
    ):
        rows.append(
            AnnualSalaryRow(
                fiscal_year=int(match.group(1)),
                maximum_salary=parse_money_cell(match.group(2)),
                median_salary=parse_money_cell(match.group(3)),
                average_salary=parse_money_cell(match.group(4)),
                minimum_salary=parse_money_cell(match.group(5)),
            )
        )
    return rows


def parse_job_titles(body_text: str) -> list[JobTitleRow]:
    start_marker = "H1B Job Title LCA Count Maximum Salary Average Salary Minimum Salary"
    section = table_section(
        body_text,
        start_marker=start_marker,
        end_markers=(
            "View Latest H1B",
            "Grade Insights",
            "H1BGrader About",
        ),
    )
    if section.startswith(start_marker):
        section = section[len(start_marker) :]
    rows: list[JobTitleRow] = []
    for match in re.finditer(
        r"(.+?)\s+([\d,]+)\s+(\$[\d,]+|-|N/A)\s+(\$[\d,]+|-|N/A)\s+"
        r"(\$[\d,]+|-|N/A)(?=\s+[A-Z][A-Za-z&/()., -]+\s+[\d,]+\s+\$|\s*$)",
        section,
    ):
        rows.append(
            JobTitleRow(
                title=match.group(1).strip(),
                lca_count=parse_int_cell(match.group(2)),
                maximum_salary=parse_money_cell(match.group(3)),
                average_salary=parse_money_cell(match.group(4)),
                minimum_salary=parse_money_cell(match.group(5)),
            )
        )
    return rows


def parse_rate_table_from_text(
    body_text: str,
    *,
    start_marker: str,
    end_markers: tuple[str, ...],
) -> list[AnnualRateRow]:
    section = table_section(body_text, start_marker=start_marker, end_markers=end_markers)
    rows: list[AnnualRateRow] = []
    for match in re.finditer(r"\b(20\d{2})\s+([\d.]+%|N/A)\s+([\d.]+%|N/A)", section):
        rows.append(
            AnnualRateRow(
                fiscal_year=int(match.group(1)),
                approval_rate=parse_percent_cell(match.group(2)),
                denial_rate=parse_percent_cell(match.group(3)),
            )
        )
    return rows


def table_section(body_text: str, *, start_marker: str, end_markers: tuple[str, ...]) -> str:
    start = body_text.find(start_marker)
    if start < 0:
        return ""

    end_candidates = [
        body_text.find(end_marker, start + len(start_marker))
        for end_marker in end_markers
        if body_text.find(end_marker, start + len(start_marker)) >= 0
    ]
    end = min(end_candidates) if end_candidates else len(body_text)
    return body_text[start:end]


def parse_int_cell(value: str) -> int:
    if value == "-":
        return 0
    return int(value.replace(",", ""))


def parse_percent_cell(value: str) -> float | None:
    if value == "N/A":
        return None
    return float(value.rstrip("%"))


def parse_money_cell(value: str) -> int | None:
    if value in {"-", "N/A"}:
        return None
    return int(value.replace("$", "").replace(",", ""))
