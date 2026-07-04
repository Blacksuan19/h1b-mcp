from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from mcp.server.fastmcp import Context, FastMCP
from pydantic import BaseModel

from h1b_mcp.models import H1BGraderBlockedError
from h1b_mcp.responses.company import (
    build_company_grade_result,
    build_company_job_sponsorship_result,
    build_company_job_titles_result,
    build_company_salaries_result,
    build_company_sponsorship_result,
)
from h1b_mcp.service import H1BGraderService
from h1b_mcp.settings import settings

T = TypeVar("T", bound=BaseModel)


def register_company_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    async def check_h1b_sponsorship(company_name: str, ctx: Context) -> dict[str, Any]:
        """Check whether a company has H-1B sponsorship evidence."""
        return await run_company_profile_tool(
            company_name=company_name,
            ctx=ctx,
            action_name="H-1B sponsorship check",
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
        return await run_company_profile_tool(
            company_name=company_name,
            ctx=ctx,
            action_name=f"H-1B job title sponsorship check for {job_title}",
            transform=lambda company_profile: build_company_job_sponsorship_result(
                company_query=company_name,
                job_title=job_title,
                company_profile=company_profile,
            ),
        )

    @mcp.tool()
    async def get_company_profile(company_name: str, ctx: Context) -> dict[str, Any]:
        """Return the full parsed H1BGrader company profile from cache or live fetch."""
        return await run_company_profile_tool(
            company_name=company_name,
            ctx=ctx,
            action_name="company profile lookup",
            transform=lambda company_profile: company_profile,
        )

    @mcp.tool()
    async def get_company_job_titles(company_name: str, ctx: Context) -> dict[str, Any]:
        """Return sponsored job titles and salary ranges for a company."""
        return await run_company_profile_tool(
            company_name=company_name,
            ctx=ctx,
            action_name="company job titles lookup",
            transform=lambda company_profile: build_company_job_titles_result(
                company_query=company_name,
                company_profile=company_profile,
            ),
        )

    @mcp.tool()
    async def get_company_salaries(company_name: str, ctx: Context) -> dict[str, Any]:
        """Return annual H-1B salary summary rows for a company."""
        return await run_company_profile_tool(
            company_name=company_name,
            ctx=ctx,
            action_name="company salaries lookup",
            transform=lambda company_profile: build_company_salaries_result(
                company_query=company_name,
                company_profile=company_profile,
            ),
        )

    @mcp.tool()
    async def get_company_grade(company_name: str, ctx: Context) -> dict[str, Any]:
        """Return H1BGrader grade, confidence, and insight data for a company."""
        return await run_company_profile_tool(
            company_name=company_name,
            ctx=ctx,
            action_name="company grade lookup",
            transform=lambda company_profile: build_company_grade_result(
                company_query=company_name,
                company_profile=company_profile,
            ),
        )


async def run_company_profile_tool(
    *,
    company_name: str,
    ctx: Context,
    action_name: str,
    transform: Callable[[Any], T],
) -> dict[str, Any]:
    async def action(service: H1BGraderService) -> T:
        company_profile = await service.get_company_profile(company_name, logger=ctx)
        return transform(company_profile)

    return await run_company_tool(
        company_name=company_name,
        ctx=ctx,
        action_name=action_name,
        action=action,
    )


async def run_company_tool(
    *,
    company_name: str,
    ctx: Context,
    action_name: str,
    action: Callable[[H1BGraderService], Awaitable[T]],
    transform: Callable[[T], BaseModel] | None = None,
) -> dict[str, Any]:
    service = H1BGraderService(settings)
    try:
        await ctx.info(f"Starting {action_name} for {company_name}.")
        result = await action(service)
        output = transform(result) if transform else result
        await ctx.info(f"Finished {action_name} for {company_name}.")
        return output.model_dump(mode="json")
    except H1BGraderBlockedError as exc:
        await ctx.warning("H1BGrader blocked the live browser lookup.")
        return blocked_payload(company_name=company_name, url=exc.url, message=str(exc))
    except Exception as exc:
        await ctx.error(f"{action_name} failed: {exc}")
        return blocked_payload(
            company_name=company_name,
            url=None,
            message=f"Live H1BGrader lookup failed before data was parsed: {exc}",
        )


def blocked_payload(*, company_name: str, url: str | None, message: str) -> dict[str, Any]:
    return {
        "company_query": company_name,
        "signal": "Blocked",
        "url": url,
        "evidence": [message],
    }
