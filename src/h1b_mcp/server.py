from typing import Any

from mcp.server.fastmcp import FastMCP

from h1b_mcp.h1bgrader import H1BGraderClient
from h1b_mcp.models import H1BGraderBlockedError, H1BLookupResult
from h1b_mcp.settings import settings

INSTRUCTIONS = """
Use this server for live H1BGrader company sponsorship checks. The tool opens
H1BGrader with SeleniumBase UC for each lookup and does not keep a local
employer database. If H1BGrader presents human verification or a block page,
report the Blocked result instead of guessing from memory or cached data.
""".strip()

mcp = FastMCP(name="h1b-mcp", instructions=INSTRUCTIONS)


@mcp.tool()
async def check_h1b_sponsorship(company_name: str) -> dict[str, Any]:
    """Search H1BGrader live for a company and return the parsed H-1B sponsor signal."""
    client = H1BGraderClient(settings)
    try:
        result = await client.check_company(company_name)
    except H1BGraderBlockedError as exc:
        result = H1BLookupResult(
            company_query=company_name,
            signal="Blocked",
            url=exc.url,
            evidence=[str(exc)],
            caveats=[
                "No sponsor conclusion was inferred because the live site blocked automation.",
                "Retry later or verify the company manually on H1BGrader.",
            ],
        )
    except Exception as exc:
        result = H1BLookupResult(
            company_query=company_name,
            signal="Blocked",
            evidence=[f"Live H1BGrader lookup failed before a sponsor signal was parsed: {exc}"],
            caveats=[
                "No sponsor conclusion was inferred.",
                "The site UI may have changed, the page may have timed out, or browser access "
                "may require manual verification.",
            ],
        )
    return result.model_dump(mode="json")


def main() -> None:
    mcp.run("stdio")
