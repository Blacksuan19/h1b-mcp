from typing import Any

from mcp.server.fastmcp import Context, FastMCP

from h1b_mcp.responses.company import (
    build_company_grade_result,
    build_company_job_sponsorship_result,
    build_company_job_titles_result,
    build_company_lca_trends_result,
    build_company_role_sponsorship_context_result,
    build_company_salaries_result,
    build_company_sponsorship_result,
)
from h1b_mcp.tools.common import run_profile_tool, run_tool


def register_company_tools(mcp: FastMCP) -> None:
    """Register all company-profile-backed tools on a FastMCP server instance."""

    @mcp.tool()
    async def check_h1b_sponsorship(company_name: str, ctx: Context) -> dict[str, Any]:
        """Check whether a company has H-1B sponsorship evidence."""
        return await run_profile_tool(
            query=company_name,
            query_field="company_query",
            ctx=ctx,
            action_name="H-1B sponsorship check",
            get_profile=lambda service: service.get_company_profile(company_name, logger=ctx),
            transform=lambda company_profile: build_company_sponsorship_result(
                company_query=company_name,
                company_profile=company_profile,
            ),
        )

    @mcp.tool()
    async def check_company_job_sponsorship(
        company_name: str,
        job_title: str,
        ctx: Context,
    ) -> dict[str, Any]:
        """Check whether a company has sponsored H-1B evidence for a job title."""
        return await run_profile_tool(
            query=company_name,
            query_field="company_query",
            ctx=ctx,
            action_name=f"H-1B job title sponsorship check for {job_title}",
            get_profile=lambda service: service.get_company_profile(company_name, logger=ctx),
            transform=lambda company_profile: build_company_job_sponsorship_result(
                company_query=company_name,
                job_title=job_title,
                company_profile=company_profile,
            ),
        )

    @mcp.tool()
    async def get_company_profile(company_name: str, ctx: Context) -> dict[str, Any]:
        """Return the full parsed H1BGrader company profile from cache or live fetch."""
        return await run_profile_tool(
            query=company_name,
            query_field="company_query",
            ctx=ctx,
            action_name="company profile lookup",
            get_profile=lambda service: service.get_company_profile(company_name, logger=ctx),
            transform=lambda company_profile: company_profile,
        )

    @mcp.tool()
    async def get_company_role_sponsorship_context(
        company_name: str,
        job_title: str,
        ctx: Context,
    ) -> dict[str, Any]:
        """Return company-specific and market-wide H-1B context for a role."""

        async def action(service: Any) -> Any:
            company_profile = await service.get_company_profile(company_name, logger=ctx)
            job_title_profile = await service.get_job_title_profile(job_title, logger=ctx)
            return build_company_role_sponsorship_context_result(
                company_query=company_name,
                job_title_query=job_title,
                company_profile=company_profile,
                job_title_profile=job_title_profile,
            )

        return await run_tool(
            query=company_name,
            query_field="company_query",
            ctx=ctx,
            action_name=f"company role sponsorship context lookup for {job_title}",
            action=action,
        )

    @mcp.tool()
    async def get_company_job_titles(company_name: str, ctx: Context) -> dict[str, Any]:
        """Return sponsored job titles and salary ranges for a company."""
        return await run_profile_tool(
            query=company_name,
            query_field="company_query",
            ctx=ctx,
            action_name="company job titles lookup",
            get_profile=lambda service: service.get_company_profile(company_name, logger=ctx),
            transform=lambda company_profile: build_company_job_titles_result(
                company_query=company_name,
                company_profile=company_profile,
            ),
        )

    @mcp.tool()
    async def get_company_lca_trends(company_name: str, ctx: Context) -> dict[str, Any]:
        """Return annual LCA approval, denial, and rate rows for a company."""
        return await run_profile_tool(
            query=company_name,
            query_field="company_query",
            ctx=ctx,
            action_name="company LCA trends lookup",
            get_profile=lambda service: service.get_company_profile(company_name, logger=ctx),
            transform=lambda company_profile: build_company_lca_trends_result(
                company_query=company_name,
                company_profile=company_profile,
            ),
        )

    @mcp.tool()
    async def get_company_salaries(company_name: str, ctx: Context) -> dict[str, Any]:
        """Return annual H-1B salary summary rows for a company."""
        return await run_profile_tool(
            query=company_name,
            query_field="company_query",
            ctx=ctx,
            action_name="company salaries lookup",
            get_profile=lambda service: service.get_company_profile(company_name, logger=ctx),
            transform=lambda company_profile: build_company_salaries_result(
                company_query=company_name,
                company_profile=company_profile,
            ),
        )

    @mcp.tool()
    async def get_company_grade(company_name: str, ctx: Context) -> dict[str, Any]:
        """Return H1BGrader grade, confidence, and insight data for a company."""
        return await run_profile_tool(
            query=company_name,
            query_field="company_query",
            ctx=ctx,
            action_name="company grade lookup",
            get_profile=lambda service: service.get_company_profile(company_name, logger=ctx),
            transform=lambda company_profile: build_company_grade_result(
                company_query=company_name,
                company_profile=company_profile,
            ),
        )
