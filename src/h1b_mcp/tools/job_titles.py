from typing import Any

from mcp.server.fastmcp import Context, FastMCP

from h1b_mcp.responses.aggregate import (
    build_job_title_employers_result,
    build_job_title_salaries_result,
    build_job_title_sponsorship_result,
)
from h1b_mcp.tools.common import run_profile_tool


def register_job_title_tools(mcp: FastMCP) -> None:
    """Register all job-title aggregate profile tools on a FastMCP server instance."""

    @mcp.tool()
    async def check_h1b_job_title_sponsorship(
        job_title: str,
        ctx: Context,
    ) -> dict[str, Any]:
        """Check whether a job title has H-1B sponsorship evidence across employers."""
        return await run_profile_tool(
            query=job_title,
            query_field="job_title_query",
            ctx=ctx,
            action_name="job title sponsorship check",
            get_profile=lambda service: service.get_job_title_profile(job_title, logger=ctx),
            transform=lambda job_title_profile: build_job_title_sponsorship_result(
                job_title_query=job_title,
                job_title_profile=job_title_profile,
            ),
        )

    @mcp.tool()
    async def get_h1b_job_title_employers(
        job_title: str,
        ctx: Context,
        limit: int = 20,
    ) -> dict[str, Any]:
        """Return top H-1B sponsoring employers for a job title."""
        return await run_profile_tool(
            query=job_title,
            query_field="job_title_query",
            ctx=ctx,
            action_name="job title employers lookup",
            get_profile=lambda service: service.get_job_title_profile(job_title, logger=ctx),
            transform=lambda job_title_profile: build_job_title_employers_result(
                job_title_query=job_title,
                job_title_profile=job_title_profile,
                limit=limit,
            ),
        )

    @mcp.tool()
    async def get_h1b_job_title_salary(
        job_title: str,
        ctx: Context,
    ) -> dict[str, Any]:
        """Return annual H-1B salary summary rows for a job title."""
        return await run_profile_tool(
            query=job_title,
            query_field="job_title_query",
            ctx=ctx,
            action_name="job title salary lookup",
            get_profile=lambda service: service.get_job_title_profile(job_title, logger=ctx),
            transform=lambda job_title_profile: build_job_title_salaries_result(
                job_title_query=job_title,
                job_title_profile=job_title_profile,
            ),
        )
