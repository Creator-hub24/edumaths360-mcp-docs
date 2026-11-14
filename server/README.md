# Edumaths360 Practice Server

A Model Context Protocol (MCP) server that gives an AI assistant three practice tools for CAT, MBA and other competitive-exam aspirants preparing quantitative aptitude and reasoning:

| Tool | What it does |
|---|---|
| `generate_problem` | Creates a seeded, reproducible problem for a topic and difficulty (easy, medium, hard): percentages, profit and loss, ratio and proportion, time-speed-distance, time and work, interest, linear and quadratic equations, number system, and number series. |
| `check_answer` | Marks an attempt and gives feedback. Never reveals the answer on an early wrong attempt. |
| `get_hint` | Returns progressive hints (levels 1–3) that never state the final answer. |

It also exposes the `syllabus://section/{section}` (quant or reasoning) and `syllabus://topics` resources and a `socratic_tutor` prompt.

```bash
uv venv && uv pip install -e ".[dev]"
uv run pytest                 # run the tests
uv run edumaths360-mcp        # start the server on stdio (it waits for a client)
```

Full documentation lives in the [docs site](../docs-site/).
