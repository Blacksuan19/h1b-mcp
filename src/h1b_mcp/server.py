from mcp.server.fastmcp import FastMCP

from h1b_mcp.tools.company import register_company_tools
from h1b_mcp.tools.job_titles import register_job_title_tools
from h1b_mcp.tools.locations import register_location_tools

INSTRUCTIONS = """
Use this server to check H-1B sponsorship evidence for companies, job titles,
and cities using H1BGrader profile data. Prefer focused tools for specific
questions and full-profile tools only when broader reasoning needs the parsed
profile. If H1BGrader requires human verification or blocks lookup, the tool
raises an error instead of guessing.
""".strip()

mcp = FastMCP(name="h1b-mcp", instructions=INSTRUCTIONS)
register_company_tools(mcp)
register_job_title_tools(mcp)
register_location_tools(mcp)


def main() -> None:
    mcp.run("stdio")
