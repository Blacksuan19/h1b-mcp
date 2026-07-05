from collections.abc import Awaitable, Callable
from typing import Annotated, TypeVar

from mcp.server.fastmcp import Context
from pydantic import BaseModel, Field

from h1b_mcp.models import H1BGraderBlockedError
from h1b_mcp.service import H1BGraderService
from h1b_mcp.settings import settings

T = TypeVar("T", bound=BaseModel)
TProfile = TypeVar("TProfile", bound=BaseModel)

CompanyQuery = Annotated[
    str,
    Field(
        description="Company or employer name. Example: Databricks.",
        examples=["Databricks", "Cloudflare", "Microsoft"],
    ),
]
JobTitleQuery = Annotated[
    str,
    Field(
        description="Job title to search. Use the role title as written or a close variant.",
        examples=["Machine Learning Engineer", "Senior Software Engineer", "Data Scientist"],
    ),
]
LocationQuery = Annotated[
    str,
    Field(
        description=(
            "City name only. Do not include state, province, or country. "
            "Use Chicago, not Chicago, IL."
        ),
        examples=["Chicago", "San Francisco", "New York"],
    ),
]


async def run_profile_tool(
    *,
    query: str,
    ctx: Context,
    action_name: str,
    get_profile: Callable[[H1BGraderService], Awaitable[TProfile]],
    transform: Callable[[TProfile], T],
) -> T:
    """Fetch a cached profile once, then project it into a tool response."""

    async def action(service: H1BGraderService) -> T:
        profile = await get_profile(service)
        return transform(profile)

    return await run_tool(
        query=query,
        ctx=ctx,
        action_name=action_name,
        action=action,
    )


async def run_tool(
    *,
    query: str,
    ctx: Context,
    action_name: str,
    action: Callable[[H1BGraderService], Awaitable[T]],
) -> T:
    """Common MCP wrapper for logging and service construction."""
    service = H1BGraderService(settings)
    try:
        await ctx.info(f"Starting {action_name} for {query}.")
        result = await action(service)
        await ctx.info(f"Finished {action_name} for {query}.")
        return result
    except H1BGraderBlockedError as exc:
        await ctx.warning("H1BGrader blocked the live browser lookup.")
        raise RuntimeError(f"H1BGrader blocked the live browser lookup: {exc}") from exc
    except Exception as exc:
        await ctx.error(f"{action_name} failed: {exc}")
        raise RuntimeError(f"Live H1BGrader lookup failed before data was parsed: {exc}") from exc
