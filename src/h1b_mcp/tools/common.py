from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from mcp.server.fastmcp import Context
from pydantic import BaseModel

from h1b_mcp.models import H1BGraderBlockedError
from h1b_mcp.service import H1BGraderService
from h1b_mcp.settings import settings

T = TypeVar("T", bound=BaseModel)
TProfile = TypeVar("TProfile", bound=BaseModel)


async def run_profile_tool(
    *,
    query: str,
    query_field: str,
    ctx: Context,
    action_name: str,
    get_profile: Callable[[H1BGraderService], Awaitable[TProfile]],
    transform: Callable[[TProfile], T],
) -> dict[str, Any]:
    """Fetch a cached profile once, then project it into a tool response."""

    async def action(service: H1BGraderService) -> T:
        profile = await get_profile(service)
        return transform(profile)

    return await run_tool(
        query=query,
        query_field=query_field,
        ctx=ctx,
        action_name=action_name,
        action=action,
    )


async def run_tool(
    *,
    query: str,
    query_field: str,
    ctx: Context,
    action_name: str,
    action: Callable[[H1BGraderService], Awaitable[T]],
) -> dict[str, Any]:
    """Common MCP wrapper for logging, service construction, and blocked payloads."""
    service = H1BGraderService(settings)
    try:
        await ctx.info(f"Starting {action_name} for {query}.")
        result = await action(service)
        await ctx.info(f"Finished {action_name} for {query}.")
        return result.model_dump(mode="json")
    except H1BGraderBlockedError as exc:
        await ctx.warning("H1BGrader blocked the live browser lookup.")
        return blocked_payload(query=query, query_field=query_field, url=exc.url, message=str(exc))
    except Exception as exc:
        await ctx.error(f"{action_name} failed: {exc}")
        return blocked_payload(
            query=query,
            query_field=query_field,
            url=None,
            message=f"Live H1BGrader lookup failed before data was parsed: {exc}",
        )


def blocked_payload(
    *,
    query: str,
    query_field: str,
    url: str | None,
    message: str,
) -> dict[str, Any]:
    """Return a consistent payload when no reliable parsed profile can be produced."""
    return {
        query_field: query,
        "signal": "Blocked",
        "url": url,
        "evidence": [message],
    }
