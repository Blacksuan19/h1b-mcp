from mcp.server.fastmcp import FastMCP

from h1b_mcp.tools.company import register_company_tools
from h1b_mcp.tools.job_titles import register_job_title_tools
from h1b_mcp.tools.locations import register_location_tools

INSTRUCTIONS = """
Use this server for live H1BGrader sponsorship checks and profile views for
companies, job titles, and locations. The server opens H1BGrader with
SeleniumBase UC when a fresh profile is needed. Parsed profiles are cached
locally and reused by later tool calls until stale. If H1BGrader presents human
verification or a block page, report the Blocked result instead of guessing.
""".strip()

mcp = FastMCP(name="h1b-mcp", instructions=INSTRUCTIONS)
register_company_tools(mcp)
register_job_title_tools(mcp)
register_location_tools(mcp)


def main() -> None:
    mcp.run("stdio")
