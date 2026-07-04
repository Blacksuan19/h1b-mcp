from mcp.server.fastmcp import FastMCP

from h1b_mcp.tools.company import register_company_tools

INSTRUCTIONS = """
Use this server for live H1BGrader company sponsorship checks and company profile
views. The server opens H1BGrader with SeleniumBase UC when a fresh company
profile is needed. Parsed company profiles are cached locally and reused by
later tool calls until stale. If H1BGrader presents human verification or a
block page, report the Blocked result instead of guessing.
""".strip()

mcp = FastMCP(name="h1b-mcp", instructions=INSTRUCTIONS)
register_company_tools(mcp)


def main() -> None:
    mcp.run("stdio")
