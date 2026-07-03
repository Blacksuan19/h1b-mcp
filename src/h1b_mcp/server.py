from typing import Any

from mcp.server.fastmcp import Context, FastMCP

from h1b_mcp.models import H1BGraderBlockedError, H1BLookupResult
from h1b_mcp.service import H1BGraderService
from h1b_mcp.settings import settings

INSTRUCTIONS = """
Use this server for live H1BGrader company sponsorship checks. The tool opens
H1BGrader with SeleniumBase UC when a fresh company profile is needed. Parsed
company profiles are cached locally and reused by later tool calls until stale.
If H1BGrader presents human verification or a block page, report the Blocked
result instead of guessing.
""".strip()

mcp = FastMCP(name="h1b-mcp", instructions=INSTRUCTIONS)


@mcp.tool()
async def check_h1b_sponsorship(company_name: str, ctx: Context) -> dict[str, Any]:
    """Search H1BGrader live for a company and return the parsed H-1B sponsor signal."""
    service = H1BGraderService(settings)
    try:
        result = await service.check_company(company_name, logger=ctx)
        await ctx.info(f"Finished H-1B sponsorship check with signal: {result.signal}.")
    except H1BGraderBlockedError as exc:
        await ctx.warning("H1BGrader blocked the live browser lookup.")
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
        await ctx.error(f"Live H1BGrader lookup failed: {exc}")
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
