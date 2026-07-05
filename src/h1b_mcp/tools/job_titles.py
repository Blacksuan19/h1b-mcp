from mcp.server.fastmcp import Context, FastMCP

from h1b_mcp.models import (
    JobTitleEmployersResult,
    JobTitleLCATrendsResult,
    JobTitleProfile,
    JobTitleSalariesResult,
    JobTitleSponsorshipResult,
)
from h1b_mcp.responses.aggregate import (
    build_job_title_employers_result,
    build_job_title_lca_trends_result,
    build_job_title_salaries_result,
    build_job_title_sponsorship_result,
)
from h1b_mcp.tools.common import JobTitleQuery, run_profile_tool


def register_job_title_tools(mcp: FastMCP) -> None:
    """Register all job-title aggregate profile tools on a FastMCP server instance."""

    @mcp.tool()
    async def check_h1b_job_title_sponsorship(
        job_title: JobTitleQuery,
        ctx: Context,
    ) -> JobTitleSponsorshipResult:
        """Use to check whether a job title has H-1B activity across employers."""
        return await run_profile_tool(
            query=job_title,
            ctx=ctx,
            action_name="job title sponsorship check",
            get_profile=lambda service: service.get_job_title_profile(job_title, logger=ctx),
            transform=lambda job_title_profile: build_job_title_sponsorship_result(
                job_title_query=job_title,
                job_title_profile=job_title_profile,
            ),
        )

    @mcp.tool()
    async def get_h1b_job_title_profile(
        job_title: JobTitleQuery,
        ctx: Context,
    ) -> JobTitleProfile:
        """Use when answering requires the complete source-backed job-title profile."""
        return await run_profile_tool(
            query=job_title,
            ctx=ctx,
            action_name="job title profile lookup",
            get_profile=lambda service: service.get_job_title_profile(job_title, logger=ctx),
            transform=lambda job_title_profile: job_title_profile,
        )

    @mcp.tool()
    async def get_h1b_job_title_employers(
        job_title: JobTitleQuery,
        ctx: Context,
        limit: int = 20,
    ) -> JobTitleEmployersResult:
        """Use to find employers that sponsor H-1B workers for a job title."""
        return await run_profile_tool(
            query=job_title,
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
    async def get_h1b_job_title_lca_trends(
        job_title: JobTitleQuery,
        ctx: Context,
    ) -> JobTitleLCATrendsResult:
        """Use to inspect annual LCA approval and denial trends for a job title."""
        return await run_profile_tool(
            query=job_title,
            ctx=ctx,
            action_name="job title LCA trends lookup",
            get_profile=lambda service: service.get_job_title_profile(job_title, logger=ctx),
            transform=lambda job_title_profile: build_job_title_lca_trends_result(
                job_title_query=job_title,
                job_title_profile=job_title_profile,
            ),
        )

    @mcp.tool()
    async def get_h1b_job_title_salary(
        job_title: JobTitleQuery,
        ctx: Context,
    ) -> JobTitleSalariesResult:
        """Use to inspect H-1B salary ranges for a job title."""
        return await run_profile_tool(
            query=job_title,
            ctx=ctx,
            action_name="job title salary lookup",
            get_profile=lambda service: service.get_job_title_profile(job_title, logger=ctx),
            transform=lambda job_title_profile: build_job_title_salaries_result(
                job_title_query=job_title,
                job_title_profile=job_title_profile,
            ),
        )
