from mcp.server.fastmcp import Context, FastMCP

from h1b_mcp.models import (
    LocationEmployersResult,
    LocationLCATrendsResult,
    LocationProfile,
    LocationSalariesResult,
    LocationSponsorshipResult,
)
from h1b_mcp.responses.aggregate import (
    build_location_employers_result,
    build_location_lca_trends_result,
    build_location_salaries_result,
    build_location_sponsorship_result,
)
from h1b_mcp.tools.common import LocationQuery, run_profile_tool


def register_location_tools(mcp: FastMCP) -> None:
    """Register all location aggregate profile tools on a FastMCP server instance."""

    @mcp.tool()
    async def check_h1b_location_sponsorship(
        location: LocationQuery,
        ctx: Context,
    ) -> LocationSponsorshipResult:
        """Use to check whether a city has H-1B activity across employers."""
        return await run_profile_tool(
            query=location,
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
        location: LocationQuery,
        ctx: Context,
    ) -> LocationProfile:
        """Use when answering requires the complete source-backed H-1B profile for a city."""
        return await run_profile_tool(
            query=location,
            ctx=ctx,
            action_name="location profile lookup",
            get_profile=lambda service: service.get_location_profile(location, logger=ctx),
            transform=lambda location_profile: location_profile,
        )

    @mcp.tool()
    async def get_h1b_location_employers(
        location: LocationQuery,
        ctx: Context,
        limit: int = 20,
    ) -> LocationEmployersResult:
        """Use to find employers that sponsor H-1B workers in a city."""
        return await run_profile_tool(
            query=location,
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
        location: LocationQuery,
        ctx: Context,
    ) -> LocationLCATrendsResult:
        """Use to inspect annual LCA approval and denial trends in a city."""
        return await run_profile_tool(
            query=location,
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
        location: LocationQuery,
        ctx: Context,
    ) -> LocationSalariesResult:
        """Use to inspect H-1B salary ranges in a city."""
        return await run_profile_tool(
            query=location,
            ctx=ctx,
            action_name="location salary lookup",
            get_profile=lambda service: service.get_location_profile(location, logger=ctx),
            transform=lambda location_profile: build_location_salaries_result(
                location_query=location,
                location_profile=location_profile,
            ),
        )
