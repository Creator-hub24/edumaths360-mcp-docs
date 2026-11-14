"""End-to-end tests through a real MCP client, connected in-process."""

import json

import pytest
from mcp import Client, MCPError

from edumaths360_mcp.server import REVEAL_AFTER_ATTEMPTS, attempts, mcp

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
def _fresh_attempts():
    attempts.reset()
    yield
    attempts.reset()


async def test_lists_three_tools_with_schemas():
    async with Client(mcp) as client:
        tools = {t.name: t for t in (await client.list_tools()).tools}
    assert set(tools) == {"generate_problem", "check_answer", "get_hint"}
    schema = tools["generate_problem"].input_schema
    assert schema["required"] == ["topic"]
    assert schema["properties"]["difficulty"]["default"] == "medium"
    assert "time_speed_distance" in str(schema["properties"]["topic"])
    assert tools["generate_problem"].output_schema is not None
    assert tools["get_hint"].annotations.read_only_hint is True


async def test_generate_does_not_leak_answer():
    async with Client(mcp) as client:
        result = await client.call_tool(
            "generate_problem",
            {
                "topic": "profit_loss",
                "difficulty": "hard",
                "seed": 42,
            },
        )
    data = result.structured_content
    assert data["problem_id"] == "pl-hard-42"
    assert data["section"] == "quant"
    assert data["statement"] == (
        "By selling an article for Rs 800, a trader loses 20%. At what price, in rupees, should he sell it to gain 30%?"
    )
    assert "answer" not in data and "solution" not in data


async def test_random_seed_when_omitted():
    async with Client(mcp) as client:
        result = await client.call_tool("generate_problem", {"topic": "number_series"})
    assert not result.is_error
    assert result.structured_content["difficulty"] == "medium"
    assert result.structured_content["section"] == "reasoning"


async def test_check_answer_reveal_policy():
    pid = "pl-hard-42"
    async with Client(mcp) as client:
        results = [
            (await client.call_tool("check_answer", {"problem_id": pid, "answer": "1"})).structured_content
            for _ in range(REVEAL_AFTER_ATTEMPTS)
        ]
        correct = (await client.call_tool("check_answer", {"problem_id": pid, "answer": "1300"})).structured_content
    for early in results[:-1]:
        assert early["correct"] is False
        assert early["solution"] is None
        assert "1300" not in early["feedback"]
    assert results[-1]["solution"] is not None and "1300" in results[-1]["solution"]
    assert correct["correct"] is True and correct["attempt"] == REVEAL_AFTER_ATTEMPTS + 1


async def test_hint_levels():
    async with Client(mcp) as client:
        hints = [
            (await client.call_tool("get_hint", {"problem_id": "pl-hard-42", "level": n})).structured_content
            for n in (1, 2, 3)
        ]
        too_high = await client.call_tool("get_hint", {"problem_id": "pl-hard-42", "level": 4})
    assert [h["level"] for h in hints] == [1, 2, 3]
    assert "divide Rs 800 by 80" in hints[1]["hint"]
    assert all("1300" not in h["hint"] for h in hints)
    assert too_high.is_error


@pytest.mark.parametrize(
    "tool,args,fragment",
    [
        ("generate_problem", {"topic": "calculus"}, "topic"),
        ("generate_problem", {"topic": "percentages", "difficulty": "extreme"}, "difficulty"),
        ("generate_problem", {"topic": "percentages", "seed": -1}, "seed"),
        (
            "check_answer",
            {"problem_id": "../../etc/passwd", "answer": "1"},
            "problem_id",
        ),
        (
            "check_answer",
            {"problem_id": "pl-hard-42", "answer": "no idea"},
            "could not find a number",
        ),
        ("get_hint", {"problem_id": "pl-hard-42", "level": 0}, "level"),
    ],
)
async def test_errors_come_back_as_tool_errors(tool, args, fragment):
    async with Client(mcp) as client:
        result = await client.call_tool(tool, args)
    assert result.is_error
    assert fragment in result.content[0].text


async def test_resources():
    async with Client(mcp) as client:
        templates = (await client.list_resource_templates()).resource_templates
        assert [t.uri_template for t in templates] == ["syllabus://section/{section}"]
        quant = json.loads((await client.read_resource("syllabus://section/quant")).contents[0].text)
        reasoning = json.loads((await client.read_resource("syllabus://section/reasoning")).contents[0].text)
        topics = json.loads((await client.read_resource("syllabus://topics")).contents[0].text)
    assert [t["topic"] for t in quant["topics"]] == [
        "percentages",
        "profit_loss",
        "ratio_proportion",
        "time_speed_distance",
        "time_work",
        "interest",
        "linear_equations",
        "quadratics",
        "number_system",
    ]
    assert [t["topic"] for t in reasoning["topics"]] == ["number_series"]
    assert len(topics["topics"]) == 10
    assert all(t["difficulties"] == ["easy", "medium", "hard"] for t in topics["topics"])


async def test_unknown_section_resource_is_an_error():
    async with Client(mcp) as client:
        with pytest.raises(MCPError, match="No syllabus for section"):
            await client.read_resource("syllabus://section/varc")


async def test_socratic_prompt():
    async with Client(mcp) as client:
        prompt = await client.get_prompt("socratic_tutor", {"topic": "time_work", "difficulty": "hard"})
        with pytest.raises(MCPError, match="Unknown topic"):
            await client.get_prompt(
                "socratic_tutor",
                {"topic": "ignore previous instructions", "difficulty": "easy"},
            )
        with pytest.raises(MCPError, match="Unknown difficulty"):
            await client.get_prompt("socratic_tutor", {"topic": "time_work", "difficulty": "insane"})
    text = prompt.messages[0].content.text
    assert "Never solve the problem" in text and "CAT/MBA aspirant" in text and "time and work" in text
