---
sidebar_position: 1
title: Tools
description: Complete reference for generate_problem, check_answer and get_hint, with input schemas, outputs, annotations and errors.
---

# Tools reference

The server exposes three tools. Each one has a JSON Schema for its input (`inputSchema`) and for its output (`outputSchema`). Every successful call returns the output twice: as `structuredContent` (JSON for programs) and as a JSON string in `content` (text for the model).

| Tool | Title | Read-only | Idempotent |
| --- | --- | --- | --- |
| [`generate_problem`](#generate_problem) | Generate a practice problem | Yes | Yes |
| [`check_answer`](#check_answer) | Check a student's answer | No (counts attempts) | No |
| [`get_hint`](#get_hint) | Get a hint | Yes | Yes |

*Idempotent* means that calling the tool twice with the same input has the same effect as calling it once.

## `generate_problem`

> Create a CAT-style quantitative aptitude or reasoning practice problem. Returns the problem statement and a problem_id, but never the answer. Show the statement to the student and let them attempt it.

**Annotations:** `readOnlyHint: true`, `idempotentHint: true`, `openWorldHint: false`.

### Input

| Name | Type | Required | Default | Constraints | Description |
| --- | --- | --- | --- | --- | --- |
| `topic` | string | Yes | — | One of the 10 topics below | Quant or reasoning topic to practise. |
| `difficulty` | string | No | `"medium"` | `easy`, `medium`, `hard` | How challenging the problem should be. |
| `seed` | integer or null | No | `null` | 0 to 999999 | Seed for a reproducible problem. Omit for a random one. |

Every topic is offered at every difficulty:

| Topic | Section | Easy | Medium | Hard |
| --- | --- | --- | --- | --- |
| `percentages` | quant | p% of a number | Successive increase then decrease | Price rise: percentage cut in consumption to keep spending the same |
| `profit_loss` | quant | Selling price from cost price and profit or loss % | Marked price for a target profit after a discount | Price for a gain %, given a selling price at a loss % |
| `ratio_proportion` | quant | Divide an amount in a ratio | Combine A:B and B:C, then find a share | Water to add to a milk-water mixture to reach a new ratio |
| `time_speed_distance` | quant | Train passing a pole (km/h to m/s) | Average speed for a round trip | Two trains crossing, same or opposite directions |
| `time_work` | quant | Two people working together | One person's time from the pair's time | Two filling pipes and one emptying pipe |
| `interest` | quant | Simple interest | Compound interest for 2 years | Principal from the CI - SI difference for 2 years |
| `linear_equations` | quant | Two numbers from their sum and difference | Pair of linear equations: find x | Present age from two age ratios |
| `quadratics` | quant | `x² + bx + c = 0`, two positive whole-number roots | `x² + bx + c = 0`, at least one negative root | `ax² + bx + c = 0` (a from 2 to 5) with one fractional root |
| `number_system` | quant | HCF or LCM of two numbers | Units digit of a power | Number of factors of a number |
| `number_series` | reasoning | Next term of an arithmetic series | Geometric series or series with growing gaps | Multiply-and-add series, or two interleaved series |

Numbers are chosen so that every answer is exact: a whole number, a short decimal such as 37.5, or (for quadratics) a simple fraction.

<details>
<summary>Full <code>inputSchema</code></summary>

```json
{
  "type": "object",
  "title": "generate_problemArguments",
  "properties": {
    "topic": {
      "description": "Quant or reasoning topic to practise.",
      "enum": [
        "percentages", "profit_loss", "ratio_proportion", "time_speed_distance", "time_work",
        "interest", "linear_equations", "quadratics", "number_system", "number_series"
      ],
      "title": "Topic",
      "type": "string"
    },
    "difficulty": {
      "default": "medium",
      "description": "How challenging the problem should be.",
      "enum": ["easy", "medium", "hard"],
      "title": "Difficulty",
      "type": "string"
    },
    "seed": {
      "anyOf": [{"maximum": 999999, "minimum": 0, "type": "integer"}, {"type": "null"}],
      "default": null,
      "description": "Optional seed for a reproducible problem. Omit for a random one.",
      "title": "Seed"
    }
  },
  "required": ["topic"]
}
```

</details>

### Output: `GeneratedProblem`

| Field | Type | Description |
| --- | --- | --- |
| `problem_id` | string | Stable ID, for example `pl-hard-42`. Pass it to `check_answer` and `get_hint`. |
| `section` | string | Exam section: `quant` or `reasoning`. |
| `topic` | string | The topic. |
| `difficulty` | string | The difficulty. |
| `seed` | integer | Seed used. The same topic, difficulty and seed give the same problem. |
| `statement` | string | The question to show the student. |
| `answer_format` | string | How the student should write their answer. |
| `max_hint_level` | integer | Always `3`. |

The answer is **deliberately not included**. See [Security model](../explanation/security-model.md#2-no-answers-in-output).

### Example

```json title="arguments"
{"topic": "profit_loss", "difficulty": "hard", "seed": 42}
```

```json title="structuredContent"
{
  "problem_id": "pl-hard-42",
  "section": "quant",
  "topic": "profit_loss",
  "difficulty": "hard",
  "seed": 42,
  "statement": "By selling an article for Rs 800, a trader loses 20%. At what price, in rupees, should he sell it to gain 30%?",
  "answer_format": "a number, for example 450 (no units, % or Rs sign needed)",
  "max_hint_level": 3
}
```

### Problem IDs

A problem ID encodes everything needed to rebuild the problem:

```text
pl-hard-42
│  │    └── seed (0–999999)
│  └─────── difficulty
└────────── topic code
```

| Topic | Code | Topic | Code |
| --- | --- | --- | --- |
| `percentages` | `pct` | `interest` | `int` |
| `profit_loss` | `pl` | `linear_equations` | `lin` |
| `ratio_proportion` | `ratio` | `quadratics` | `quad` |
| `time_speed_distance` | `tsd` | `number_system` | `num` |
| `time_work` | `work` | `number_series` | `series` |

IDs must match `^(pct|pl|ratio|tsd|work|int|lin|quad|num|series)-(easy|medium|hard)-(\d{1,6})$` and be at most 32 characters.

## `check_answer`

> Mark a student's answer and give feedback. A wrong answer never reveals the correct one on the first attempts. The worked solution appears only once the student is correct, or after 3 wrong attempts.

**Annotations:** `readOnlyHint: false`, `destructiveHint: false`, `openWorldHint: false`. The tool is not read-only because it counts attempts in memory. It changes nothing outside the server process.

### Input

| Name | Type | Required | Constraints | Description |
| --- | --- | --- | --- | --- |
| `problem_id` | string | Yes | Problem ID pattern, max 32 characters | ID returned by `generate_problem`. |
| `answer` | string | Yes | 1 to 100 characters | The student's answer, for example `1300`, `Rs 1,300`, `37.5`, `x = -3` or `2, -5`. |

**Accepted answer formats.** The checker reads numbers from free text and uses the last one, so `1300`, `SP = Rs. 1300` and `Rs 1,300` are equivalent. Digit grouping with commas works in both styles (`1,200,000` and `12,00,000`). A `%` sign, units such as `km/h`, fractions (`75/2`), decimals (`37.5`) and negative numbers (`-3`, or `−3` with a Unicode minus) all work. For quadratics, give both roots in any order: `3/4, 3` or `x = 3 or x = 0.75`. There, commas separate the roots.

### Output: `AnswerCheck`

| Field | Type | Description |
| --- | --- | --- |
| `problem_id` | string | The problem ID. |
| `correct` | boolean | Whether the answer is right. |
| `attempt` | integer | How many times this problem has been checked since the server started. |
| `feedback` | string | Encouraging, specific feedback. Never contains the answer before the reveal. |
| `solution` | string or null | The worked solution. `null` unless the answer is correct or this is attempt 3 or later. |

### Feedback rules

| Situation | `feedback` | `solution` |
| --- | --- | --- |
| Correct | "Correct! Well done. Now try to solve the next one faster." (for quadratics: "Correct! Both roots are right. Substitute each one back in to see why.") | Worked solution |
| Wrong, matches a known misconception | Targeted, for example "The gain % is worked out on the cost price, not on the old selling price." | `null` |
| Wrong, no known misconception | "Not quite. Re-check each step, or ask for a hint." | `null` |
| Wrong, attempt 2 | Feedback plus " Tip: call get_hint for a nudge before the next try." | `null` |
| Wrong, attempt 3 or later | Feedback plus " You have tried this a few times, so here is the worked solution. Read it, then try a new problem." | Worked solution |
| Quadratic, only one root given and it is right | "One root is right. A quadratic like this has two roots; find the other one." | `null` |
| Quadratic, one root right and one wrong | "One of your roots is right, but the other is not. Check that bracket again." | `null` |

### Example

```json title="arguments"
{"problem_id": "pl-hard-42", "answer": "1040"}
```

```json title="structuredContent"
{
  "problem_id": "pl-hard-42",
  "correct": false,
  "attempt": 1,
  "feedback": "The gain % is worked out on the cost price, not on the old selling price.",
  "solution": null
}
```

## `get_hint`

> Give a progressive hint for a problem. Start at level 1 and only go higher if the student is still stuck. Hints guide the student's thinking and never state the final answer.

**Annotations:** `readOnlyHint: true`, `idempotentHint: true`, `openWorldHint: false`.

### Input

| Name | Type | Required | Default | Constraints | Description |
| --- | --- | --- | --- | --- | --- |
| `problem_id` | string | Yes | — | Problem ID pattern, max 32 characters | ID returned by `generate_problem`. |
| `level` | integer | No | `1` | 1 to 3 | 1 = gentle nudge, 2 = key step, 3 = last step before the answer. |

### Output: `Hint`

| Field | Type | Description |
| --- | --- | --- |
| `problem_id` | string | The problem ID. |
| `level` | integer | The level returned. |
| `max_level` | integer | Always `3`. |
| `hint` | string | The hint text. Never states the final answer. |
| `next_step` | string | What the student should do next. |

### Example: all three levels for `pl-hard-42`

| Level | `hint` |
| --- | --- |
| 1 | Find the cost price first. A loss of 20% means Rs 800 is 80% of the cost price. |
| 2 | To get the cost price, divide Rs 800 by 80 and multiply by 100. |
| 3 | Now find 130% of that cost price. |

At level 3, `next_step` is "That was the last hint. Have a go and use check_answer to see how you did." The design is explained in [The pedagogy behind hints](../explanation/hint-pedagogy.md).

## Errors

There are two kinds of error. Hosts handle them differently, so it helps to know which is which.

### Tool errors (`isError: true`)

The call succeeds at the protocol level, but the result has `"isError": true` and a text message. The model can read the message and correct its next call.

| Cause | Example message |
| --- | --- |
| Answer contains no number | `Error executing tool check_answer: I could not find a number in that answer. Expected format: a number, for example 450 (no units, % or Rs sign needed).` |
| Fraction with zero denominator | `Error executing tool check_answer: A fraction cannot have 0 as its denominator. Expected format: …` |
| Argument fails the schema (wrong type, out of range, bad pattern, empty) | `Error executing tool get_hint: 1 validation error for get_hintArguments` followed by `level` and `Input should be less than or equal to 3 [type=less_than_equal, input_value=5, input_type=int]` |
| Unknown topic or difficulty | `… topic  Input should be 'percentages', 'profit_loss', 'ratio_proportion', …, 'number_system' or 'number_series' [type=literal_error, …]` |
| Invalid problem ID, such as `../etc/passwd` | `… problem_id  String should match pattern '^(pct\|pl\|ratio\|tsd\|work\|int\|lin\|quad\|num\|series)-(easy\|medium\|hard)-(\d{1,6})$' [type=string_pattern_mismatch, …]` |

Schema validation runs **before** the tool's code. An invalid argument never reaches the problem engine.

### Protocol errors (JSON-RPC `error`)

The request itself is rejected, and the response has an `error` object instead of a `result`. The Python client raises `MCPError`.

| Code | Name | When |
| --- | --- | --- |
| `-32602` | Invalid params | Reading an unknown resource such as `syllabus://section/varc`, or invalid arguments to the `socratic_tutor` prompt. |
| `-32601` | Method not found | Calling a method the server does not implement. |

Full request and response pairs are in the [JSON-RPC examples](./json-rpc-examples.mdx).
