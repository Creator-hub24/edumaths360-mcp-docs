"""Edumaths360 Practice Server.

An MCP server that lets an AI assistant run maths practice for Class 6-10
students without doing the thinking for them.

Run it with ``edumaths360-mcp`` (or ``python -m edumaths360_mcp``). It speaks
MCP over stdio, so stdout is reserved for protocol messages: all logging goes
to stderr.
"""

from __future__ import annotations

import json
import logging
import secrets
import sys
from collections import OrderedDict
from typing import Annotated

from mcp import MCPError
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ResourceNotFoundError, ToolError
from mcp.types import INVALID_PARAMS, ToolAnnotations
from pydantic import BaseModel, Field

from edumaths360_mcp import __version__
from edumaths360_mcp.problems import (
    DIFFICULTIES,
    MAX_GRADE,
    MAX_HINT_LEVEL,
    MAX_SEED,
    MIN_GRADE,
    PROBLEM_ID_PATTERN,
    TOPIC_DESCRIPTIONS,
    TOPIC_GRADES,
    TOPICS,
    Difficulty,
    ProblemError,
    Topic,
    check,
    generate,
    problem_from_id,
)

logger = logging.getLogger("edumaths360_mcp")

#: Wrong attempts allowed before check_answer shows the worked solution.
REVEAL_AFTER_ATTEMPTS = 3
#: Upper bound on how many problems we remember attempt counts for.
MAX_TRACKED_PROBLEMS = 10_000

mcp = MCPServer(
    name="edumaths360-practice",
    title="Edumaths360 Practice Server",
    version=__version__,
    instructions=(
        "Maths practice for Class 6-10 students. Use generate_problem to create a problem, "
        "let the student attempt it, and use check_answer to mark it. If the student is stuck, "
        "call get_hint with level 1 first and only move to higher levels if they are still stuck. "
        "Do not solve the problem for the student yourself."
    ),
)


# --------------------------------------------------------------------- outputs


class GeneratedProblem(BaseModel):
    """A new practice problem. The answer is deliberately not included."""

    problem_id: str = Field(description="Stable ID. Pass it to check_answer and get_hint.")
    topic: str
    grade: int
    difficulty: str
    seed: int = Field(description="Seed used. The same topic, grade, difficulty and seed give the same problem.")
    statement: str = Field(description="The question to show the student.")
    answer_format: str = Field(description="How the student should write their answer.")
    max_hint_level: int


class AnswerCheck(BaseModel):
    """The result of marking one attempt."""

    problem_id: str
    correct: bool
    attempt: int = Field(description="How many times this problem has been checked in this session.")
    feedback: str = Field(description="Encouraging, specific feedback. Never contains the answer before the reveal.")
    solution: str | None = Field(
        default=None,
        description=f"Worked solution. Only present when correct, or after {REVEAL_AFTER_ATTEMPTS} wrong attempts.",
    )


class Hint(BaseModel):
    """One step of guidance. Hints never state the final answer."""

    problem_id: str
    level: int
    max_level: int
    hint: str
    next_step: str


# ------------------------------------------------------------------ state


class AttemptTracker:
    """Counts attempts per problem, in memory, with a hard size limit.

    Bounded so a misbehaving client cannot grow memory without limit.
    """

    def __init__(self, max_items: int = MAX_TRACKED_PROBLEMS) -> None:
        self._counts: OrderedDict[str, int] = OrderedDict()
        self._max_items = max_items

    def record(self, problem_id: str) -> int:
        count = self._counts.pop(problem_id, 0) + 1
        self._counts[problem_id] = count
        while len(self._counts) > self._max_items:
            self._counts.popitem(last=False)
        return count

    def reset(self) -> None:
        self._counts.clear()


attempts = AttemptTracker()


# ------------------------------------------------------------------- tools

GENERATE_PROBLEM_DESCRIPTION = (
    "Create a maths practice problem for a Class 6-10 student. Returns the problem statement and a "
    "problem_id, but never the answer. Show the statement to the student and let them attempt it."
)
CHECK_ANSWER_DESCRIPTION = (
    "Mark a student's answer and give feedback. A wrong answer never reveals the correct one on the "
    "first attempts. The worked solution appears only once the student is correct, or after "
    f"{REVEAL_AFTER_ATTEMPTS} wrong attempts."
)
GET_HINT_DESCRIPTION = (
    "Give a progressive hint for a problem. Start at level 1 and only go higher if the student is "
    "still stuck. Hints guide the student's thinking and never state the final answer."
)


@mcp.tool(
    title="Generate a practice problem",
    description=GENERATE_PROBLEM_DESCRIPTION,
    annotations=ToolAnnotations(read_only_hint=True, idempotent_hint=True, open_world_hint=False),
)
def generate_problem(
    topic: Annotated[Topic, Field(description="Maths topic to practise.")],
    grade: Annotated[
        int,
        Field(ge=MIN_GRADE, le=MAX_GRADE, description="Student's class (grade), 6 to 10."),
    ],
    difficulty: Annotated[Difficulty, Field(description="How challenging the problem should be.")] = "medium",
    seed: Annotated[
        int | None,
        Field(
            ge=0,
            le=MAX_SEED,
            description="Optional seed for a reproducible problem. Omit for a random one.",
        ),
    ] = None,
) -> GeneratedProblem:
    if seed is None:
        seed = secrets.randbelow(MAX_SEED + 1)
    try:
        problem = generate(topic, grade, difficulty, seed)
    except ProblemError as exc:
        raise ToolError(str(exc)) from exc
    logger.info("generated %s", problem.id)
    return GeneratedProblem(
        problem_id=problem.id,
        topic=problem.topic,
        grade=problem.grade,
        difficulty=problem.difficulty,
        seed=problem.seed,
        statement=problem.statement,
        answer_format=problem.answer_format,
        max_hint_level=MAX_HINT_LEVEL,
    )


@mcp.tool(
    title="Check a student's answer",
    description=CHECK_ANSWER_DESCRIPTION,
    annotations=ToolAnnotations(read_only_hint=False, destructive_hint=False, open_world_hint=False),
)
def check_answer(
    problem_id: Annotated[
        str,
        Field(
            pattern=PROBLEM_ID_PATTERN,
            max_length=32,
            description="ID returned by generate_problem.",
        ),
    ],
    answer: Annotated[
        str,
        Field(
            min_length=1,
            max_length=100,
            description="The student's answer, e.g. '7', 'x = -3', '5/14', '2, -5'.",
        ),
    ],
) -> AnswerCheck:
    try:
        problem = problem_from_id(problem_id)
        result = check(problem, answer)
    except ProblemError as exc:
        raise ToolError(str(exc)) from exc

    attempt = attempts.record(problem.id)
    solution = None
    feedback = result.feedback
    if result.correct:
        solution = problem.solution
    elif attempt >= REVEAL_AFTER_ATTEMPTS:
        solution = problem.solution
        feedback += " You have tried this a few times, so here is the worked solution. Read it, then try a new problem."
    elif attempt == REVEAL_AFTER_ATTEMPTS - 1:
        feedback += " Tip: call get_hint for a nudge before the next try."
    logger.info("checked %s attempt=%d correct=%s", problem.id, attempt, result.correct)
    return AnswerCheck(
        problem_id=problem.id,
        correct=result.correct,
        attempt=attempt,
        feedback=feedback,
        solution=solution,
    )


@mcp.tool(
    title="Get a hint",
    description=GET_HINT_DESCRIPTION,
    annotations=ToolAnnotations(read_only_hint=True, idempotent_hint=True, open_world_hint=False),
)
def get_hint(
    problem_id: Annotated[
        str,
        Field(
            pattern=PROBLEM_ID_PATTERN,
            max_length=32,
            description="ID returned by generate_problem.",
        ),
    ],
    level: Annotated[
        int,
        Field(
            ge=1,
            le=MAX_HINT_LEVEL,
            description="1 = gentle nudge, 2 = key step, 3 = last step before the answer.",
        ),
    ] = 1,
) -> Hint:
    try:
        problem = problem_from_id(problem_id)
    except ProblemError as exc:
        raise ToolError(str(exc)) from exc
    next_step = (
        f"Try the problem again. If still stuck, ask for level {level + 1}."
        if level < MAX_HINT_LEVEL
        else "That was the last hint. Have a go and use check_answer to see how you did."
    )
    return Hint(
        problem_id=problem.id,
        level=level,
        max_level=MAX_HINT_LEVEL,
        hint=problem.hints[level - 1],
        next_step=next_step,
    )


# --------------------------------------------------------------- resources


def _grade_syllabus(grade: int) -> dict:
    return {
        "grade": grade,
        "topics": [
            {
                "topic": t,
                "description": TOPIC_DESCRIPTIONS[t],
                "difficulties": list(DIFFICULTIES),
            }
            for t in TOPICS
            if grade in TOPIC_GRADES[t]
        ],
    }


@mcp.resource(
    "syllabus://topics",
    title="All topics",
    description="Every topic the server can generate, with the grades it is offered for.",
    mime_type="application/json",
)
def all_topics() -> str:
    data = [
        {
            "topic": t,
            "description": TOPIC_DESCRIPTIONS[t],
            "grades": list(TOPIC_GRADES[t]),
        }
        for t in TOPICS
    ]
    return json.dumps({"topics": data}, indent=2)


@mcp.resource(
    "syllabus://grade/{grade}",
    title="Syllabus for one grade",
    description="Topics and difficulty levels available for a Class 6-10 grade.",
    mime_type="application/json",
)
def grade_syllabus(grade: str) -> str:
    if not grade.isdigit() or not MIN_GRADE <= int(grade) <= MAX_GRADE:
        raise ResourceNotFoundError(f"No syllabus for grade '{grade}'. Use a grade from {MIN_GRADE} to {MAX_GRADE}.")
    return json.dumps(_grade_syllabus(int(grade)), indent=2)


# ----------------------------------------------------------------- prompts


@mcp.prompt(
    title="Socratic maths tutor",
    description="Run a practice session where the assistant asks guiding questions instead of giving answers.",
)
def socratic_tutor(topic: str = "linear_equations", grade: str = "8") -> str:
    # Prompt arguments are free text from the client. Validate them before they
    # are pasted into instructions for the model (prompt-injection defence).
    if topic not in TOPICS:
        raise MCPError(INVALID_PARAMS, f"Unknown topic '{topic}'. Choose one of: {', '.join(TOPICS)}.")
    if not grade.isdigit() or int(grade) not in TOPIC_GRADES[topic]:
        raise MCPError(INVALID_PARAMS, f"'{topic}' is offered for grades {list(TOPIC_GRADES[topic])}; got '{grade}'.")
    return (
        f"You are a patient maths tutor for a Class {grade} student practising {topic.replace('_', ' ')}.\n\n"
        "Rules:\n"
        f"1. Call generate_problem with topic='{topic}' and grade={grade}, then show the student the statement.\n"
        "2. Never solve the problem for the student and never state the final answer yourself.\n"
        "3. Ask one short guiding question at a time, for example 'What operation undoes + 7?'.\n"
        "4. When the student gives an answer, call check_answer and share the feedback in your own words.\n"
        "5. If the student is stuck, call get_hint starting at level 1. Only go to the next level "
        "if they are still stuck after trying.\n"
        "6. Praise effort and method, not only correct answers.\n\n"
        "Start by greeting the student and generating the first problem."
    )


# -------------------------------------------------------------------- main


def main() -> None:
    logging.basicConfig(
        stream=sys.stderr,  # stdout carries JSON-RPC messages; never log there
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    logger.info("Starting Edumaths360 Practice Server %s on stdio", __version__)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
