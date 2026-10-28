"""Keep the code shown in the documentation working.

The tutorial server and the "Add a new tool" example live in snippets/ and are
quoted in the docs, so CI runs them here.
"""

import importlib.util
import sys
from pathlib import Path

import pytest
from mcp import Client, StdioServerParameters

pytestmark = pytest.mark.anyio

SNIPPETS = Path(__file__).resolve().parents[2] / "snippets"


@pytest.fixture
def anyio_backend():
    return "asyncio"


async def test_tutorial_server_over_stdio():
    params = StdioServerParameters(command=sys.executable, args=[str(SNIPPETS / "tutorial" / "times_table_server.py")])
    async with Client(params) as client:
        tools = await client.list_tools()
        assert [t.name for t in tools.tools] == ["times_table"]
        result = await client.call_tool("times_table", {"number": 7, "up_to": 3})
        assert result.structured_content == {"result": ["7 × 1 = 7", "7 × 2 = 14", "7 × 3 = 21"]}
        bad = await client.call_tool("times_table", {"number": 50})
        assert bad.is_error
        about = await client.read_resource("tables://about")
        assert "times_table" in about.contents[0].text


async def test_extend_server_adds_worksheet_tool():
    spec = importlib.util.spec_from_file_location("extend_server", SNIPPETS / "extend_server.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    try:
        await _check_worksheet(module.mcp)
    finally:
        module.mcp.remove_tool("make_worksheet")  # keep the shared server unchanged for other tests


async def _check_worksheet(server):
    async with Client(server) as client:
        names = [t.name for t in (await client.list_tools()).tools]
        assert "make_worksheet" in names
        result = await client.call_tool("make_worksheet", {"topic": "fractions", "grade": 7, "count": 3})
        sheet = result.structured_content
        assert sheet["title"] == "Class 7 fractions (easy)"
        assert [i["problem_id"] for i in sheet["items"]] == ["frac-g7-easy-1", "frac-g7-easy-2", "frac-g7-easy-3"]
        assert all(set(item) == {"problem_id", "statement"} for item in sheet["items"])  # no answers
        bad = await client.call_tool("make_worksheet", {"topic": "quadratics", "grade": 6})
        assert bad.is_error
