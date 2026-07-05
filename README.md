# H1B MCP

[![PyPI](https://img.shields.io/pypi/v/h1b-mcp.svg)](https://pypi.org/project/h1b-mcp/)
[![Python](https://img.shields.io/pypi/pyversions/h1b-mcp.svg)](https://pypi.org/project/h1b-mcp/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Typed](https://img.shields.io/badge/typed-py.typed-green.svg)](src/h1b_mcp/py.typed)

Live H-1B sponsorship checks for Codex and other MCP-compatible agents.

`h1b-mcp` opens H1BGrader in a real browser, searches for companies, job
titles, and locations, extracts profile tables, and returns normalized
sponsorship signals with structured evidence.

> This is an independent community project. It is not affiliated with,
> authorized by, endorsed by, or sponsored by H1BGrader.

## Features

- Live H1BGrader company, job-title, and location lookup through SeleniumBase UC mode.
- Structured H-1B sponsor signal: `Strong signal`, `Mixed signal`,
  `Weak signal`, `No sponsor`, or `Blocked`.
- Parsed annual LCA approvals and denial counts.
- Parsed annual LCA approval and denial rates.
- Parsed annual USCIS H-1B approvals and denial counts.
- Parsed annual USCIS approval and denial rates.
- Parsed annual H-1B salary maximum, median, average, and minimum.
- Parsed H1BGrader grade, confidence, annual grades, and grade insight cards.
- Parsed latest H-1B job title counts and salary ranges.
- Parsed job-title and location aggregate profiles with top employers, LCA
  trends, approval rates, and salary history.
- Local caches so repeated checks can reuse parsed H1BGrader data.
- Typed Pydantic response models that are easy for agents to consume.
- Browser-block aware behavior that returns `Blocked` instead of inventing a
  sponsor conclusion.

## Included Tools

### Company Tools

<table>
  <thead>
    <tr>
      <th>Tool</th>
      <th>Description</th>
      <th>Output Shape</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>check_h1b_sponsorship</code></td>
      <td>Classify company-level H-1B sponsorship evidence.</td>
      <td>
<details>
<summary>JSON shape</summary>

<pre lang="json"><code>{
  "company_query": "string",
  "matched_company": "string | null",
  "signal": "string",
  "url": "string | null",
  "evidence": ["string"]
}</code></pre>

</details>
      </td>
    </tr>
    <tr>
      <td><code>check_company_job_sponsorship</code></td>
      <td>Check whether a company has sponsored evidence for a specific job title.</td>
      <td>
<details>
<summary>JSON shape</summary>

<pre lang="json"><code>{
  "company_query": "string",
  "matched_company": "string | null",
  "job_title_query": "string",
  "signal": "string",
  "url": "string | null",
  "matches": ["JobTitleMatch"],
  "company_signal": "string",
  "evidence": ["string"]
}</code></pre>

</details>
      </td>
    </tr>
    <tr>
      <td><code>get_company_role_sponsorship_context</code></td>
      <td>Return company-specific and market-wide context for a role.</td>
      <td>
<details>
<summary>JSON shape</summary>

<pre lang="json"><code>{
  "company_query": "string",
  "matched_company": "string | null",
  "company_signal": "string",
  "company_role_signal": "string",
  "market_signal": "string",
  "company_role_matches": ["JobTitleMatch"],
  "market_top_employers": ["EmployerFilingRow"]
}</code></pre>

</details>
      </td>
    </tr>
    <tr>
      <td><code>get_company_profile</code></td>
      <td>Return the full parsed company profile.</td>
      <td>
<details>
<summary>JSON shape</summary>

<pre lang="json"><code>{
  "query": "string",
  "matched_name": "string | null",
  "url": "string",
  "fetched_at": "datetime",
  "profile": "H1BGraderProfile"
}</code></pre>

</details>
      </td>
    </tr>
    <tr>
      <td><code>get_company_job_titles</code></td>
      <td>Return sponsored job titles for a company.</td>
      <td>
<details>
<summary>JSON shape</summary>

<pre lang="json"><code>{
  "company_query": "string",
  "matched_company": "string | null",
  "url": "string | null",
  "job_titles": ["JobTitleRow"]
}</code></pre>

</details>
      </td>
    </tr>
    <tr>
      <td><code>get_company_lca_trends</code></td>
      <td>Return annual company LCA trend rows.</td>
      <td>
<details>
<summary>JSON shape</summary>

<pre lang="json"><code>{
  "company_query": "string",
  "matched_company": "string | null",
  "url": "string | null",
  "lca_approvals": ["AnnualCountRow"],
  "lca_approval_rates": ["AnnualRateRow"]
}</code></pre>

</details>
      </td>
    </tr>
    <tr>
      <td><code>get_company_uscis_trends</code></td>
      <td>Return annual company USCIS trend rows.</td>
      <td>
<details>
<summary>JSON shape</summary>

<pre lang="json"><code>{
  "company_query": "string",
  "matched_company": "string | null",
  "url": "string | null",
  "uscis_approvals": ["AnnualCountRow"],
  "uscis_approval_rates": ["AnnualRateRow"]
}</code></pre>

</details>
      </td>
    </tr>
    <tr>
      <td><code>get_company_salaries</code></td>
      <td>Return annual H-1B salary history for a company.</td>
      <td>
<details>
<summary>JSON shape</summary>

<pre lang="json"><code>{
  "company_query": "string",
  "matched_company": "string | null",
  "url": "string | null",
  "salaries": ["AnnualSalaryRow"]
}</code></pre>

</details>
      </td>
    </tr>
    <tr>
      <td><code>get_company_grade</code></td>
      <td>Return H1BGrader grade details for a company.</td>
      <td>
<details>
<summary>JSON shape</summary>

<pre lang="json"><code>{
  "company_query": "string",
  "matched_company": "string | null",
  "url": "string | null",
  "grade": "GradeProfile | null"
}</code></pre>

</details>
      </td>
    </tr>
  </tbody>
</table>

### Job Title Tools

<table>
  <thead>
    <tr>
      <th>Tool</th>
      <th>Description</th>
      <th>Output Shape</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>check_h1b_job_title_sponsorship</code></td>
      <td>Classify market-level H-1B sponsorship evidence for a job title.</td>
      <td>
<details>
<summary>JSON shape</summary>

<pre lang="json"><code>{
  "job_title_query": "string",
  "matched_job_title": "string | null",
  "signal": "string",
  "url": "string | null",
  "evidence": ["string"],
  "latest_lca": "AnnualCountRow | null",
  "latest_approval_rate": "AnnualRateRow | null",
  "latest_salary": "AnnualSalaryRow | null",
  "top_employers": ["EmployerFilingRow"]
}</code></pre>

</details>
      </td>
    </tr>
    <tr>
      <td><code>get_h1b_job_title_profile</code></td>
      <td>Return the full parsed job-title profile.</td>
      <td>
<details>
<summary>JSON shape</summary>

<pre lang="json"><code>{
  "query": "string",
  "matched_name": "string | null",
  "url": "string",
  "fetched_at": "datetime",
  "profile": "H1BGraderAggregateProfile"
}</code></pre>

</details>
      </td>
    </tr>
    <tr>
      <td><code>get_h1b_job_title_employers</code></td>
      <td>Return top H-1B sponsoring employers for a job title.</td>
      <td>
<details>
<summary>JSON shape</summary>

<pre lang="json"><code>{
  "job_title_query": "string",
  "matched_job_title": "string | null",
  "url": "string | null",
  "employers": ["EmployerFilingRow"]
}</code></pre>

</details>
      </td>
    </tr>
    <tr>
      <td><code>get_h1b_job_title_lca_trends</code></td>
      <td>Return annual job-title LCA trend rows.</td>
      <td>
<details>
<summary>JSON shape</summary>

<pre lang="json"><code>{
  "job_title_query": "string",
  "matched_job_title": "string | null",
  "url": "string | null",
  "lca_approvals": ["AnnualCountRow"],
  "lca_approval_rates": ["AnnualRateRow"]
}</code></pre>

</details>
      </td>
    </tr>
    <tr>
      <td><code>get_h1b_job_title_salary</code></td>
      <td>Return annual H-1B salary history for a job title.</td>
      <td>
<details>
<summary>JSON shape</summary>

<pre lang="json"><code>{
  "job_title_query": "string",
  "matched_job_title": "string | null",
  "url": "string | null",
  "salaries": ["AnnualSalaryRow"]
}</code></pre>

</details>
      </td>
    </tr>
  </tbody>
</table>

### Location Tools

<table>
  <thead>
    <tr>
      <th>Tool</th>
      <th>Description</th>
      <th>Output Shape</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>check_h1b_location_sponsorship</code></td>
      <td>Classify city-level H-1B sponsorship evidence.</td>
      <td>
<details>
<summary>JSON shape</summary>

<pre lang="json"><code>{
  "location_query": "string",
  "matched_location": "string | null",
  "signal": "string",
  "url": "string | null",
  "evidence": ["string"],
  "latest_lca": "AnnualCountRow | null",
  "latest_approval_rate": "AnnualRateRow | null",
  "latest_salary": "AnnualSalaryRow | null",
  "top_employers": ["EmployerFilingRow"]
}</code></pre>

</details>
      </td>
    </tr>
    <tr>
      <td><code>get_h1b_location_profile</code></td>
      <td>Return the full parsed city profile.</td>
      <td>
<details>
<summary>JSON shape</summary>

<pre lang="json"><code>{
  "query": "string",
  "matched_name": "string | null",
  "url": "string",
  "fetched_at": "datetime",
  "profile": "H1BGraderAggregateProfile"
}</code></pre>

</details>
      </td>
    </tr>
    <tr>
      <td><code>get_h1b_location_employers</code></td>
      <td>Return top H-1B sponsoring employers for a city.</td>
      <td>
<details>
<summary>JSON shape</summary>

<pre lang="json"><code>{
  "location_query": "string",
  "matched_location": "string | null",
  "url": "string | null",
  "employers": ["EmployerFilingRow"]
}</code></pre>

</details>
      </td>
    </tr>
    <tr>
      <td><code>get_h1b_location_lca_trends</code></td>
      <td>Return annual city LCA trend rows.</td>
      <td>
<details>
<summary>JSON shape</summary>

<pre lang="json"><code>{
  "location_query": "string",
  "matched_location": "string | null",
  "url": "string | null",
  "lca_approvals": ["AnnualCountRow"],
  "lca_approval_rates": ["AnnualRateRow"]
}</code></pre>

</details>
      </td>
    </tr>
    <tr>
      <td><code>get_h1b_location_salary</code></td>
      <td>Return annual H-1B salary history for a city.</td>
      <td>
<details>
<summary>JSON shape</summary>

<pre lang="json"><code>{
  "location_query": "string",
  "matched_location": "string | null",
  "url": "string | null",
  "salaries": ["AnnualSalaryRow"]
}</code></pre>

</details>
      </td>
    </tr>
  </tbody>
</table>

## Quick Start

Run the published package with `uvx`:

```bash
uvx h1b-mcp@latest
```

Lookups use SeleniumBase UC mode. The first lookup may download or prepare a
compatible ChromeDriver automatically.

## Codex Setup

Add the server to your Codex MCP config:

```toml
[mcp_servers.h1b]
command = "uvx"
args = ["h1b-mcp@latest"]
env = { UV_HTTP_TIMEOUT = "300" }
tool_timeout_sec = 300
```

Or add it from the CLI:

```bash
codex mcp add h1b --env UV_HTTP_TIMEOUT=300 -- uvx h1b-mcp@latest
```

Restart Codex and check `/mcp` to confirm the server is available.

## Local Development Setup

Install dependencies:

```bash
uv sync
```

Run the server locally:

```bash
uv run h1b-mcp
```

Use a local checkout from Codex before publishing:

```toml
[mcp_servers.h1b]
command = "uv"
args = ["run", "--project", "/path/to/h1b-mcp", "h1b-mcp"]
tool_timeout_sec = 300
```

## Usage

Ask your MCP client to check a company:

```text
Check whether Databricks sponsors H-1B visas.
```

The MCP tool call is:

```python
check_h1b_sponsorship(company_name="Databricks")
```

Example response shape:

```json
{
  "company_query": "Databricks",
  "matched_company": "Databricks Inc",
  "signal": "Strong signal",
  "url": "https://h1bgrader.com/h1b-sponsors/databricks-inc-nokpn1vn04",
  "evidence": [
    "Latest LCA table reports 174 filings in fiscal year 2026, including 173 certified and 0 denied.",
    "Latest non-empty USCIS table row reports 337 approvals and 0 denials in fiscal year 2025.",
    "H1BGrader grade tab shows latest grade A with high confidence.",
    "Job title table includes 56 sponsored title rows."
  ]
}
```

## How It Works

<details>
<summary>View request flow diagram</summary>

```mermaid
flowchart TD
    A[MCP client calls any H1B tool] --> B[FastMCP tool handler]
    B --> C[tools.common run_tool or run_profile_tool]
    C --> D[H1BGraderService]

    D --> E{Profile type}
    E --> F[get_company_profile]
    E --> G[get_job_title_profile]
    E --> H[get_location_profile]

    F --> I{Fresh cache entry?}
    G --> I
    H --> I

    I -->|Yes| J[Load typed profile from entity cache]
    I -->|No| K[H1BGraderClient fetch_profile with lookup spec]

    K --> L[Launch SeleniumBase UC homepage session]
    L --> M[Open company, job-title, or city search tab]
    M --> N[Type query into shared typeahead]
    N --> O[Click selected dropdown result]
    O --> P[Open profile tabs required by lookup spec]
    P --> Q[Parse page source into typed profile model]
    Q --> R[Write profile to matching cache]

    J --> S[Focused response builder]
    R --> S

    S --> T{Requested slice}
    T --> U[Sponsorship signal]
    T --> V[Role context]
    T --> W[Full profile]
    T --> X[Employers or job titles]
    T --> Y[LCA or USCIS trends]
    T --> Z[Salaries or grade]

    U --> AA[Return structured Pydantic output]
    V --> AA
    W --> AA
    X --> AA
    Y --> AA
    Z --> AA

    K --> AB{Cloudflare or lookup failure?}
    AB -->|Blocked or failed| AC[Raise MCP tool error with clear message]
```

</details>

1. A FastMCP tool receives a company, job-title, or location request.
2. The shared tool runner creates an `H1BGraderService` and logs progress through the MCP context.
3. The service selects the matching profile cache and checks for a fresh parsed profile.
4. On cache hit, the typed cached profile goes straight to the response builder.
5. On cache miss, the SeleniumBase UC client opens H1BGrader and runs the lookup spec for the requested entity type.
6. The lookup spec selects the correct search tab, typeahead input, expected URL pattern, tabs to open, and parser.
7. Parsers extract the available LCA, USCIS, salary, grade, job-title, or employer data into typed profile models.
8. The service stores the parsed profile in the matching local cache for later tool calls.
9. The requested tool builds a focused Pydantic response from the same cached profile data.
10. Browser blocks, missing suggestions, and unexpected lookup failures are surfaced as MCP tool errors with clear messages.

## Signals

| Signal | Meaning |
| --- | --- |
| `Strong signal` | The profile contains recent, structured approval or filing evidence. |
| `Mixed signal` | The profile contains both sponsor and denial/no-sponsor indicators. |
| `Weak signal` | The profile has limited sponsorship evidence. |
| `No sponsor` | H1BGrader indicates the company is not a sponsor or no useful profile data was found. |
| `Blocked` | Browser verification, a site block, timeout, or an unexpected live lookup failure prevented a reliable conclusion. |

## Browser Blocks

H1BGrader may still present human verification, rate limits, or other bot
protection. When that happens, `h1b-mcp` returns a `Blocked` result with a
clear evidence message instead of making a claim from memory.

The browser profile and caches are stored at:

```text
~/.h1b-mcp/browser-profile
~/.h1b-mcp/cache/company-profiles
~/.h1b-mcp/cache/job-title-profiles
~/.h1b-mcp/cache/location-profiles
```

## Current Scope

This project exposes company, job-title, and location tools backed by locally
cached parsed H1BGrader profiles. It does not ship a bundled employer database
or bulk scrape H1BGrader. H-1B source data is released periodically, so cached
profile data is usually useful for repeated analysis rather than minute-by-minute
freshness.

## Troubleshooting

| Problem | What to try |
| --- | --- |
| First lookup is slow | Wait for SeleniumBase to prepare ChromeDriver and the browser profile. |
| Tool times out | Increase your MCP client `tool_timeout_sec` to `300`. |
| Response is `Blocked` | Retry later or verify manually on H1BGrader. The server intentionally avoids guessing. |
| Local server cannot start | Run `uv sync`, then retry `uv run h1b-mcp`. |

## Development

Run the normal checks:

```bash
uv run ruff check .
uv run pyright
uv run pytest
uv build
```

Run tests only:

```bash
uv run pytest -q
```

## Versioning

Version bumps use `bumpver`:

```bash
uv run bumpver update --patch --no-fetch
uv lock
```

Use `--minor`, `--major`, or `--set-version 1.2.3` instead of `--patch` when
needed. `bumpver` is configured not to create commits, tags, or pushes.
