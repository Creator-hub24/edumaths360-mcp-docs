"""Example for the "Add a new tool" how-to guide.

Adds a make_worksheet tool to the Edumaths360 Practice Server without editing
the package, then runs the server over stdio.

Run it with:  python snippets/extend_server.py
"""

import logging
import sys
from typing import Annotated

from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import BaseModel, Field

from edumaths360_mcp.problems import MAX_SEED, Difficulty, ProblemError, Topic, generate
from edumaths360_mcp.server import mcp


class WorksheetItem(BaseModel):
    problem_id: str
    statement: str


class Worksheet(BaseModel):
    """A set of problems to print or share. Answers are not included."""

    title: str
    items: list[WorksheetItem]


@mcp.tool(
    title="Make a worksheet",
    description=(
        "Create a numbered set of practice problems on one topic. Returns statements and "
        "problem IDs only, never answers. Use check_answer to mark each one."
    ),
    annotations=ToolAnnotations(read_only_hint=True, idempotent_hint=True, open_world_hint=False),
)
def make_worksheet(
    topic: Annotated[Topic, Field(description="Maths topic to practise.")],
    grade: Annotated[int, Field(ge=6, le=10, description="Student's class (grade), 6 to 10.")],
    difficulty: Annotated[Difficulty, Field(description="How challenging the problems should be.")] = "easy",
    count: Annotated[int, Field(ge=1, le=10, description="Number of problems, 1 to 10.")] = 5,
    first_seed: Annotated[int, Field(ge=0, le=MAX_SEED - 10, description="Seed of the first problem.")] = 1,
) -> Worksheet:
    try:
        problems = [generate(topic, grade, difficulty, first_seed + i) for i in range(count)]
    except ProblemError as exc:
        raise ToolError(str(exc)) from exc
    return Worksheet(
        title=f"Class {grade} {topic.replace('_', ' ')} ({difficulty})",
        items=[WorksheetItem(problem_id=p.id, statement=p.statement) for p in problems],
    )


if __name__ == "__main__":
    logging.basicConfig(stream=sys.stderr, level=logging.INFO)
    mcp.run(transport="stdio")
