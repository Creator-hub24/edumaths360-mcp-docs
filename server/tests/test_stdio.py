"""Integration test: launch the real server process and talk to it over stdio."""

import sys

import pytest
from mcp import Client, StdioServerParameters

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


async def test_server_runs_over_stdio():
    params = StdioServerParameters(command=sys.executable, args=["-m", "edumaths360_mcp"])
    async with Client(params) as client:
        assert client.server_info.name == "edumaths360-practice"
        result = await client.call_tool(
            "generate_problem", {"topic": "fractions", "grade": 7, "difficulty": "easy", "seed": 1}
        )
        assert result.structured_content["problem_id"] == "frac-g7-easy-1"
