from typing import Any

from mcp.server.fastmcp import Context, FastMCP

from h1b_mcp.responses.aggregate import (
    build_location_employers_result,
    build_location_lca_trends_result,
    build_location_salaries_result,
    build_location_sponsorship_result,
)
from h1b_mcp.tools.common import run_profile_tool


def register_location_tools(mcp: FastMCP) -> None:
    """Register all location aggregate profile tools on a FastMCP server instance."""

    @mcp.tool()
    async def check_h1b_location_sponsorship(
        location: str,
        ctx: Context,
    ) -> dict[str, Any]:
        """Check whether a city has H-1B sponsorship evidence across employers."""
        return await run_profile_tool(
            query=location,
            query_field="location_query",
            ctx=ctx,
            action_name="location sponsorship check",
            get_profile=lambda service: service.get_location_profile(location, logger=ctx),
            transform=lambda location_profile: build_location_sponsorship_result(
                location_query=location,
                location_profile=location_profile,
            ),
        )

    @mcp.tool()
    async def get_h1b_location_profile(
        location: str,
        ctx: Context,
    ) -> dict[str, Any]:
        """Return the full parsed H1BGrader location profile from cache or live fetch."""
        return await run_profile_tool(
            query=location,
            query_field="location_query",
            ctx=ctx,
            action_name="location profile lookup",
            get_profile=lambda service: service.get_location_profile(location, logger=ctx),
            transform=lambda location_profile: location_profile,
        )

    @mcp.tool()
    async def get_h1b_location_employers(
        location: str,
        ctx: Context,
        limit: int = 20,
    ) -> dict[str, Any]:
        """Return top H-1B sponsoring employers for a city."""
        return await run_profile_tool(
            query=location,
            query_field="location_query",
            ctx=ctx,
            action_name="location employers lookup",
            get_profile=lambda service: service.get_location_profile(location, logger=ctx),
            transform=lambda location_profile: build_location_employers_result(
                location_query=location,
                location_profile=location_profile,
                limit=limit,
            ),
        )

    @mcp.tool()
    async def get_h1b_location_lca_trends(
        location: str,
        ctx: Context,
    ) -> dict[str, Any]:
        """Return annual LCA approval, denial, and rate rows for a city."""
        return await run_profile_tool(
            query=location,
            query_field="location_query",
            ctx=ctx,
            action_name="location LCA trends lookup",
            get_profile=lambda service: service.get_location_profile(location, logger=ctx),
            transform=lambda location_profile: build_location_lca_trends_result(
                location_query=location,
                location_profile=location_profile,
            ),
        )

    @mcp.tool()
    async def get_h1b_location_salary(
        location: str,
        ctx: Context,
    ) -> dict[str, Any]:
        """Return annual H-1B salary summary rows for a city."""
        return await run_profile_tool(
            query=location,
            query_field="location_query",
            ctx=ctx,
            action_name="location salary lookup",
            get_profile=lambda service: service.get_location_profile(location, logger=ctx),
            transform=lambda location_profile: build_location_salaries_result(
                location_query=location,
                location_profile=location_profile,
            ),
        )
