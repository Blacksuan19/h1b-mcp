from datetime import UTC, datetime
from pathlib import Path

from h1b_mcp.constants import COMPANY_PROFILE_CACHE_SCHEMA_VERSION
from h1b_mcp.models import CompanyProfile
from h1b_mcp.parsers.tables import parse_h1bgrader_profile
from h1b_mcp.settings import Settings

DATABRICKS_PROFILE_URL = "https://h1bgrader.com/h1b-sponsors/databricks-inc-nokpn1vn04"
DATABRICKS_PROFILE_TEXT = (
    "Databricks INC H1B Sponsorship Data "
    "Yes, Databricks INC sponsors H1B visas. "
    "H1B LCA Approvals, Denials Fiscal Year* Certified Certified Withd. "
    "Withdrawn Denied 2026 173 - 1 - 2025 376 9 - - 2024 292 33 1 - "
    "2023 211 26 1 - 2022 241 4 - - 2021 170 2 3 - 2020 68 3 - - "
    "2019 64 4 2 1 2018 39 4 3 - 2017 38 7 - - "
    "H1B LCA Approval & Denial Rates Fiscal Year* Approval (%) Denial (%) "
    "2026 100.00% 0.00% 2025 100.00% 0.00% 2019 98.55% 1.45% "
    "H1B Salaries Fiscal Year* Maximum Median Average Minimum "
    "2026 $318,781 $173,732 $175,681 $103,646 "
    "2025 $325,000 $166,962 $167,569 $106,558 "
    "Latest H1B Job Titles sponsored by Databricks INC in 2026 (H1B LCAs) "
    "H1B Job Title LCA Count Maximum Salary Average Salary Minimum Salary "
    "Software Engineer 33 $187,741 $160,905 $131,997 "
    "Sr Software Engineer 27 $226,138 $192,758 $157,000"
)
DATABRICKS_PROFILE_HTML = """
<html>
  <body>
    <h1>Databricks INC H1B Sponsorship Data</h1>
    <p>Yes, Databricks INC sponsors H1B visas.</p>
    <table>
      <tr><th colspan="5">H1B LCA Approvals, Denials</th></tr>
      <tr>
        <th>Fiscal Year*</th><th>Certified</th><th>Certified Withd.</th>
        <th>Withdrawn</th><th>Denied</th>
      </tr>
      <tr><td>2026</td><td>173</td><td>-</td><td>1</td><td>-</td></tr>
      <tr><td>2025</td><td>376</td><td>9</td><td>-</td><td>-</td></tr>
      <tr><td>2024</td><td>292</td><td>33</td><td>1</td><td>-</td></tr>
    </table>
    <table>
      <tr><th colspan="3">H1B LCA Approval &amp; Denial Rates</th></tr>
      <tr><th>Fiscal Year*</th><th>Approval (%)</th><th>Denial (%)</th></tr>
      <tr><td>2026</td><td>100.00%</td><td>0.00%</td></tr>
      <tr><td>2025</td><td>100.00%</td><td>0.00%</td></tr>
      <tr><td>2019</td><td>98.55%</td><td>1.45%</td></tr>
    </table>
    <table>
      <tr><th colspan="5">USCIS H1B Approvals, Denials</th></tr>
      <tr>
        <th>Fiscal Year*</th><th>New Approvals</th><th>Cont. Approvals</th>
        <th>New Denials</th><th>Cont. Denials</th>
      </tr>
      <tr><td>2026</td><td>-</td><td>-</td><td>-</td><td>-</td></tr>
      <tr><td>2025</td><td>70</td><td>267</td><td>-</td><td>-</td></tr>
      <tr><td>2024</td><td>81</td><td>202</td><td>-</td><td>-</td></tr>
    </table>
    <table>
      <tr><th colspan="3">USCIS H1B Approval &amp; Denial Rates</th></tr>
      <tr><th>Fiscal Year*</th><th>Approval (%)</th><th>Denial (%)</th></tr>
      <tr><td>2026</td><td>N/A</td><td>N/A</td></tr>
      <tr><td>2025</td><td>100.00%</td><td>0.00%</td></tr>
      <tr><td>2023</td><td>98.04%</td><td>1.96%</td></tr>
    </table>
    <table>
      <tr><th colspan="5">H1B Salaries</th></tr>
      <tr>
        <th>Fiscal Year*</th><th>Maximum</th><th>Median</th>
        <th>Average</th><th>Minimum</th>
      </tr>
      <tr><td>2026</td><td>$318,781</td><td>$173,732</td><td>$175,681</td><td>$103,646</td></tr>
      <tr><td>2025</td><td>$325,000</td><td>$166,962</td><td>$167,569</td><td>$106,558</td></tr>
      <tr><td>2024</td><td>$285,500</td><td>$155,000</td><td>$165,360</td><td>$110,000</td></tr>
    </table>
    <table>
      <tr>
        <th>H1B Job Title</th><th>LCA Count</th><th>Maximum Salary</th>
        <th>Average Salary</th><th>Minimum Salary</th>
      </tr>
      <tr>
        <td>Software Engineer</td><td>33</td><td>$187,741</td>
        <td>$160,905</td><td>$131,997</td>
      </tr>
      <tr>
        <td>Sr Software Engineer</td><td>27</td><td>$226,138</td>
        <td>$192,758</td><td>$157,000</td>
      </tr>
      <tr>
        <td>Solutions Architect</td><td>11</td><td>$155,522</td>
        <td>$142,134</td><td>$131,082</td>
      </tr>
    </table>
    <div id="employer-grade">
      <div class="row justify-content-center mb-3">
        <div class="col-6 border rounded">
          <p>2022 Grade</p><h3>A</h3><p>Oct 2021 - Sep 2022</p>
        </div>
        <div class="col-6 border rounded">
          <p>2023 Grade</p><h3>A</h3><p>Oct 2022 - Sep 2023</p>
        </div>
        <div class="col-6 border rounded">
          <p>2024 Grade</p><h3>A</h3><p>Oct 2023 - Sep 2024</p>
        </div>
        <div class="col-6 border rounded">
          <p><span class="confidence confidence-high">High Confidence</span></p>
        </div>
      </div>
      <div class="bs-callout bs-callout-success">
        <h4>Data availability - Very High Confidence to Grade Databricks INC</h4>
        <p>
          Based on data availability for H1B approvals with USCIS, Databricks INC
          meets our data availability criteria with a data availability score of
          100 / 100. Also, for H1B Labor Condition Applications(LCAs) data filed
          with US Department of Labor(DOL) as well, it meets our data criteria
          with a score of 100 / 100.
        </p>
      </div>
      <div class="bs-callout bs-callout-success">
        <h4>Great H1B LCA Success Record for Databricks INC</h4>
        <p>
          Based on total number of H1B Labor Condition Applications(LCAs) filed
          with US Department of Labor(DOL), Databricks INC had an overall approval
          rate of 99 / 100.
        </p>
      </div>
      <div class="bs-callout bs-callout-success">
        <h4>Great USCIS H1B Approvals Record for Databricks INC</h4>
        <p>
          Based on total number of H1B Petitions filed with USCIS for new and
          continuing employment categories of applications, Databricks INC had an
          overall approval rate of 99 / 100.
        </p>
      </div>
      <div class="bs-callout bs-callout-success">
        <h4>Databricks INC is not a H1B Dependent Employer</h4>
        <p>
          Based on the ratio of total number of employees to H1B Employees in the
          company, Databricks INC is classified as
          <span class="badge badge-success">NOT a H1B Dependent Employer</span>.
        </p>
      </div>
      <div class="bs-callout bs-callout-success">
        <h4>Databricks INC is not a Willful Violator</h4>
        <p>
          US Department of Labor(DOL) Classified Databricks INC as
          <span class="badge badge-success">NOT a Willful violator</span>.
        </p>
      </div>
    </div>
  </body>
</html>
"""


class FakeProfileFetcher:
    def __init__(self, profile: CompanyProfile) -> None:
        self.profile = profile
        self.calls: list[str] = []
        self.logger: object | None = None

    async def fetch_company_profile(
        self,
        company_name: str,
        *,
        logger: object | None = None,
    ) -> CompanyProfile:
        self.calls.append(company_name)
        self.logger = logger
        return self.profile


class FakeLogSink:
    def __init__(self) -> None:
        self.messages: list[tuple[str, str]] = []

    async def debug(self, message: str) -> None:
        self.messages.append(("debug", message))

    async def info(self, message: str) -> None:
        self.messages.append(("info", message))

    async def warning(self, message: str) -> None:
        self.messages.append(("warning", message))

    async def error(self, message: str) -> None:
        self.messages.append(("error", message))


def cache_settings(tmp_path: Path, *, cache_ttl_seconds: int = 60 * 60) -> Settings:
    return Settings(
        profile_dir=tmp_path / "browser-profile",
        cache_dir=tmp_path / "company-cache",
        cache_ttl_seconds=cache_ttl_seconds,
    )


def databricks_company_profile(*, fetched_at: datetime | None = None) -> CompanyProfile:
    return CompanyProfile(
        cache_schema_version=COMPANY_PROFILE_CACHE_SCHEMA_VERSION,
        company_query="Databricks",
        matched_company="DATABRICKS INC",
        url=DATABRICKS_PROFILE_URL,
        fetched_at=fetched_at or datetime.now(UTC),
        sponsor_status="sponsors",
        profile=parse_h1bgrader_profile(DATABRICKS_PROFILE_HTML),
    )
