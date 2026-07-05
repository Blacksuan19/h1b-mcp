from mcp.server.fastmcp import Context, FastMCP

from h1b_mcp.models import (
    CompanyGradeResult,
    CompanyJobSponsorshipResult,
    CompanyJobTitlesResult,
    CompanyLCATrendsResult,
    CompanyProfile,
    CompanyRoleSponsorshipContextResult,
    CompanySalariesResult,
    CompanySponsorshipResult,
)
from h1b_mcp.responses.company import (
    build_company_grade_result,
    build_company_job_sponsorship_result,
    build_company_job_titles_result,
    build_company_lca_trends_result,
    build_company_role_sponsorship_context_result,
    build_company_salaries_result,
    build_company_sponsorship_result,
)
from h1b_mcp.service import H1BGraderService
from h1b_mcp.tools.common import CompanyQuery, JobTitleQuery, run_profile_tool, run_tool


def register_company_tools(mcp: FastMCP) -> None:
    """Register all company-profile-backed tools on a FastMCP server instance."""

    @mcp.tool()
    async def check_h1b_sponsorship(
        company_name: CompanyQuery,
        ctx: Context,
    ) -> CompanySponsorshipResult:
        """Use to check whether an employer has H-1B sponsorship evidence."""
        return await run_profile_tool(
            query=company_name,
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
        company_name: CompanyQuery,
        job_title: JobTitleQuery,
        ctx: Context,
    ) -> CompanyJobSponsorshipResult:
        """Use to check whether an employer sponsors roles matching a job title."""
        return await run_profile_tool(
            query=company_name,
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
    async def get_company_profile(company_name: CompanyQuery, ctx: Context) -> CompanyProfile:
        """Use when answering requires the complete source-backed company profile."""
        return await run_profile_tool(
            query=company_name,
            ctx=ctx,
            action_name="company profile lookup",
            get_profile=lambda service: service.get_company_profile(company_name, logger=ctx),
            transform=lambda company_profile: company_profile,
        )

    @mcp.tool()
    async def get_company_role_sponsorship_context(
        company_name: CompanyQuery,
        job_title: JobTitleQuery,
        ctx: Context,
    ) -> CompanyRoleSponsorshipContextResult:
        """Use to gather company-specific and market-wide H-1B context for a role."""

        async def action(service: H1BGraderService) -> CompanyRoleSponsorshipContextResult:
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
            ctx=ctx,
            action_name=f"company role sponsorship context lookup for {job_title}",
            action=action,
        )

    @mcp.tool()
    async def get_company_job_titles(
        company_name: CompanyQuery,
        ctx: Context,
    ) -> CompanyJobTitlesResult:
        """Use to inspect the H-1B-sponsored roles an employer has filed for."""
        return await run_profile_tool(
            query=company_name,
            ctx=ctx,
            action_name="company job titles lookup",
            get_profile=lambda service: service.get_company_profile(company_name, logger=ctx),
            transform=lambda company_profile: build_company_job_titles_result(
                company_query=company_name,
                company_profile=company_profile,
            ),
        )

    @mcp.tool()
    async def get_company_lca_trends(
        company_name: CompanyQuery,
        ctx: Context,
    ) -> CompanyLCATrendsResult:
        """Use to inspect an employer's annual LCA approval and denial history."""
        return await run_profile_tool(
            query=company_name,
            ctx=ctx,
            action_name="company LCA trends lookup",
            get_profile=lambda service: service.get_company_profile(company_name, logger=ctx),
            transform=lambda company_profile: build_company_lca_trends_result(
                company_query=company_name,
                company_profile=company_profile,
            ),
        )

    @mcp.tool()
    async def get_company_salaries(
        company_name: CompanyQuery,
        ctx: Context,
    ) -> CompanySalariesResult:
        """Use to inspect an employer's H-1B salary ranges by fiscal year."""
        return await run_profile_tool(
            query=company_name,
            ctx=ctx,
            action_name="company salaries lookup",
            get_profile=lambda service: service.get_company_profile(company_name, logger=ctx),
            transform=lambda company_profile: build_company_salaries_result(
                company_query=company_name,
                company_profile=company_profile,
            ),
        )

    @mcp.tool()
    async def get_company_grade(company_name: CompanyQuery, ctx: Context) -> CompanyGradeResult:
        """Use to inspect an employer's H1BGrader grade and grading factors."""
        return await run_profile_tool(
            query=company_name,
            ctx=ctx,
            action_name="company grade lookup",
            get_profile=lambda service: service.get_company_profile(company_name, logger=ctx),
            transform=lambda company_profile: build_company_grade_result(
                company_query=company_name,
                company_profile=company_profile,
            ),
        )
