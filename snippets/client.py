"""Minimal Python client for the Edumaths360 Practice Server.

Launches the server as a subprocess over stdio (the same way Claude Desktop
or Cursor would), then walks through one practice round:
generate a problem -> wrong answer -> hint -> correct answer.

Usage (from the repository root, after installing the server):
    python snippets/client.py
"""

from __future__ import annotations

import asyncio
import json
import sys

from mcp import Client, StdioServerParameters

# Start the server with the same Python interpreter that runs this script.
SERVER = StdioServerParameters(command=sys.executable, args=["-m", "edumaths360_mcp"])


async def main() -> None:
    async with Client(SERVER) as client:
        info = client.server_info
        print(f"Connected to {info.title} v{info.version} (protocol {client.protocol_version})\n")

        tools = await client.list_tools()
        print("Tools:", ", ".join(tool.name for tool in tools.tools))

        # 1. Generate a reproducible problem.
        result = await client.call_tool(
            "generate_problem",
            {"topic": "linear_equations", "grade": 8, "difficulty": "medium", "seed": 42},
        )
        problem = result.structured_content
        print(f"\nProblem {problem['problem_id']}: {problem['statement']}")

        # 2. A wrong answer: feedback, but no answer revealed.
        result = await client.call_tool("check_answer", {"problem_id": problem["problem_id"], "answer": "x = -14"})
        print("Attempt 'x = -14' ->", result.structured_content["feedback"])

        # 3. Ask for progressively stronger hints.
        for level in (1, 2):
            result = await client.call_tool("get_hint", {"problem_id": problem["problem_id"], "level": level})
            print(f"Hint {level}:", result.structured_content["hint"])

        # 4. The correct answer unlocks the worked solution.
        result = await client.call_tool("check_answer", {"problem_id": problem["problem_id"], "answer": "14"})
        check = result.structured_content
        print("Attempt '14' ->", check["feedback"], "| Solution:", check["solution"])

        # 5. Errors come back as a normal result with is_error=True.
        result = await client.call_tool("generate_problem", {"topic": "quadratics", "grade": 7})
        print("\nError example ->", result.is_error, result.content[0].text)

        # 6. Read a resource and fetch a prompt.
        syllabus = await client.read_resource("syllabus://grade/9")
        topics = [t["topic"] for t in json.loads(syllabus.contents[0].text)["topics"]]
        print("Class 9 topics:", ", ".join(topics))

        prompt = await client.get_prompt("socratic_tutor", {"topic": "fractions", "grade": "7"})
        print("Prompt starts:", prompt.messages[0].content.text.splitlines()[0])


if __name__ == "__main__":
    asyncio.run(main())
