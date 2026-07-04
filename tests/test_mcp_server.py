from collections.abc import AsyncIterator
from typing import Any

import pytest
from mcp.shared.memory import create_connected_server_and_client_session

import h1b_mcp.tools.common as tool_common
from h1b_mcp.server import mcp
from h1b_mcp.settings import Settings
from tests.fixtures import (
    chicago_location_profile,
    databricks_company_profile,
    machine_learning_engineer_profile,
)


class FakeMCPService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def get_company_profile(
        self,
        company_name: str,
        *,
        force_refresh: bool = False,
        logger: object | None = None,
    ) -> Any:
        return databricks_company_profile()

    async def get_job_title_profile(
        self,
        job_title: str,
        *,
        force_refresh: bool = False,
        logger: object | None = None,
    ) -> Any:
        return machine_learning_engineer_profile()

    async def get_location_profile(
        self,
        location: str,
        *,
        force_refresh: bool = False,
        logger: object | None = None,
    ) -> Any:
        return chicago_location_profile()


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def mcp_session(monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[Any]:
    monkeypatch.setattr(tool_common, "H1BGraderService", FakeMCPService)
    async with create_connected_server_and_client_session(mcp, raise_exceptions=True) as session:
        yield session


@pytest.mark.anyio
async def test_mcp_server_lists_registered_tools(mcp_session: Any) -> None:
    result = await mcp_session.list_tools()
    tool_names = {tool.name for tool in result.tools}

    assert "check_h1b_sponsorship" in tool_names
    assert "check_h1b_job_title_sponsorship" in tool_names
    assert "check_h1b_location_sponsorship" in tool_names
    assert "get_h1b_job_title_employers" in tool_names
    assert "get_h1b_location_salary" in tool_names


@pytest.mark.anyio
async def test_mcp_company_tool_returns_structured_content(mcp_session: Any) -> None:
    result = await mcp_session.call_tool(
        "check_h1b_sponsorship",
        {"company_name": "Databricks"},
    )

    assert not result.isError
    assert result.structuredContent is not None
    assert result.structuredContent["company_query"] == "Databricks"
    assert result.structuredContent["matched_company"] == "DATABRICKS INC"
    assert result.structuredContent["signal"] == "Strong signal"


@pytest.mark.anyio
async def test_mcp_job_title_tool_returns_structured_content(mcp_session: Any) -> None:
    result = await mcp_session.call_tool(
        "check_h1b_job_title_sponsorship",
        {"job_title": "Machine Learning Engineer"},
    )

    assert not result.isError
    assert result.structuredContent is not None
    assert result.structuredContent["job_title_query"] == "Machine Learning Engineer"
    assert result.structuredContent["matched_job_title"] == "MACHINE LEARNING ENGINEER"
    assert result.structuredContent["top_employers"][0]["employer_name"] == "Adobe INC"


@pytest.mark.anyio
async def test_mcp_location_tool_returns_structured_content(mcp_session: Any) -> None:
    result = await mcp_session.call_tool(
        "get_h1b_location_employers",
        {"location": "Chicago", "limit": 1},
    )

    assert not result.isError
    assert result.structuredContent is not None
    assert result.structuredContent["location_query"] == "Chicago"
    assert result.structuredContent["matched_location"] == "CHICAGO, IL"
    assert len(result.structuredContent["employers"]) == 1
