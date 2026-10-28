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

> Create a maths practice problem for a Class 6-10 student. Returns the problem statement and a problem_id, but never the answer. Show the statement to the student and let them attempt it.

**Annotations:** `readOnlyHint: true`, `idempotentHint: true`, `openWorldHint: false`.

### Input

| Name | Type | Required | Default | Constraints | Description |
| --- | --- | --- | --- | --- | --- |
| `topic` | string | Yes | — | `linear_equations`, `fractions`, `percentages`, `quadratics` | Maths topic to practise. |
| `grade` | integer | Yes | — | 6 to 10 | Student's class (grade). |
| `difficulty` | string | No | `"medium"` | `easy`, `medium`, `hard` | How challenging the problem should be. |
| `seed` | integer or null | No | `null` | 0 to 999999 | Seed for a reproducible problem. Omit for a random one. |

Not every topic is offered for every grade:

| Topic | Grades | Easy | Medium | Hard |
| --- | --- | --- | --- | --- |
| `linear_equations` | 6–10 | `x + b = c` | `ax + b = c` | `a(x + b) = cx + d` |
| `fractions` | 6–8 | Add, same denominator | Add or subtract, different denominators | Divide |
| `percentages` | 6–10 | p% of an amount | Percentage increase or decrease | Reverse percentage (original price before a discount) |
| `quadratics` | 9–10 | `x² + bx + c = 0`, two positive whole-number roots | `x² + bx + c = 0`, at least one negative root | `ax² + bx + c = 0` (a from 2 to 5) with one fractional root |

<details>
<summary>Full <code>inputSchema</code></summary>

```json
{
  "type": "object",
  "title": "generate_problemArguments",
  "properties": {
    "topic": {
      "description": "Maths topic to practise.",
      "enum": ["linear_equations", "fractions", "percentages", "quadratics"],
      "title": "Topic",
      "type": "string"
    },
    "grade": {
      "description": "Student's class (grade), 6 to 10.",
      "maximum": 10,
      "minimum": 6,
      "title": "Grade",
      "type": "integer"
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
  "required": ["topic", "grade"]
}
```

</details>

### Output: `GeneratedProblem`

| Field | Type | Description |
| --- | --- | --- |
| `problem_id` | string | Stable ID, for example `lin-g8-medium-42`. Pass it to `check_answer` and `get_hint`. |
| `topic` | string | The topic. |
| `grade` | integer | The grade. |
| `difficulty` | string | The difficulty. |
| `seed` | integer | Seed used. The same topic, grade, difficulty and seed give the same problem. |
| `statement` | string | The question to show the student. |
| `answer_format` | string | How the student should write their answer. |
| `max_hint_level` | integer | Always `3`. |

The answer is **deliberately not included**. See [Security model](../explanation/security-model.md#2-no-answers-in-output).

### Example

```json title="arguments"
{"topic": "linear_equations", "grade": 8, "difficulty": "medium", "seed": 42}
```

```json title="structuredContent"
{
  "problem_id": "lin-g8-medium-42",
  "topic": "linear_equations",
  "grade": 8,
  "difficulty": "medium",
  "seed": 42,
  "statement": "Solve for x: 7x + 7 = 105",
  "answer_format": "a whole number, for example 7 or -3",
  "max_hint_level": 3
}
```

### Problem IDs

A problem ID encodes everything needed to rebuild the problem:

```text
lin-g8-medium-42
│   │  │      └── seed (0–999999)
│   │  └───────── difficulty
│   └──────────── grade (g6–g10)
└──────────────── topic code: lin, frac, pct or quad
```

IDs must match `^(lin|frac|pct|quad)-g([6-9]|10)-(easy|medium|hard)-(\d{1,6})$` and be at most 32 characters.

## `check_answer`

> Mark a student's answer and give feedback. A wrong answer never reveals the correct one on the first attempts. The worked solution appears only once the student is correct, or after 3 wrong attempts.

**Annotations:** `readOnlyHint: false`, `destructiveHint: false`, `openWorldHint: false`. The tool is not read-only because it counts attempts in memory. It changes nothing outside the server process.

### Input

| Name | Type | Required | Constraints | Description |
| --- | --- | --- | --- | --- |
| `problem_id` | string | Yes | Problem ID pattern, max 32 characters | ID returned by `generate_problem`. |
| `answer` | string | Yes | 1 to 100 characters | The student's answer, for example `7`, `x = -3`, `5/14` or `2, -5`. |

**Accepted answer formats.** The checker reads numbers from free text, so `14`, `x = 14` and `x=14` are equivalent. Fractions (`7/6`), decimals (`2.5`) and negative numbers (`-3`, or `−3` with a Unicode minus) all work. For quadratics, give both roots in any order: `1/3, -5` or `x = -5 or x = 1/3`.

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
| Correct | "Correct! Well done." (for quadratics: "Correct! Both roots are right. Substitute each one back in to see why.") | Worked solution |
| Correct value, fraction not simplified (for example `42/24` for `7/4`) | "Correct! Well done. Your value is right, but it is not in simplest form yet. Can you simplify it?" | Worked solution |
| Wrong, matches a known misconception | Targeted, for example "Check your signs: you have the right size of number but the wrong sign." | `null` |
| Wrong, no known misconception | "Not quite. Re-check each step, or ask for a hint." | `null` |
| Wrong, attempt 2 | Feedback plus " Tip: call get_hint for a nudge before the next try." | `null` |
| Wrong, attempt 3 or later | Feedback plus " You have tried this a few times, so here is the worked solution. Read it, then try a new problem." | Worked solution |
| Quadratic, only one root given and it is right | "One root is right. A quadratic like this has two roots; find the other one." | `null` |
| Quadratic, one root right and one wrong | "One of your roots is right, but the other is not. Check that bracket again." | `null` |

### Example

```json title="arguments"
{"problem_id": "lin-g8-medium-42", "answer": "x = -14"}
```

```json title="structuredContent"
{
  "problem_id": "lin-g8-medium-42",
  "correct": false,
  "attempt": 1,
  "feedback": "Check your signs: you have the right size of number but the wrong sign.",
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

### Example: all three levels for `lin-g8-medium-42`

| Level | `hint` |
| --- | --- |
| 1 | Undo the operations in reverse order: deal with the number added or subtracted first, then the multiplication. |
| 2 | Subtract 7 from both sides. You should get 7x = 98. |
| 3 | Now divide both sides by 7. What is 98 ÷ 7? |

At level 3, `next_step` is "That was the last hint. Have a go and use check_answer to see how you did." The design is explained in [The pedagogy behind hints](../explanation/hint-pedagogy.md).

## Errors

There are two kinds of error. Hosts handle them differently, so it helps to know which is which.

### Tool errors (`isError: true`)

The call succeeds at the protocol level, but the result has `"isError": true` and a text message. The model can read the message and correct its next call.

| Cause | Example message |
| --- | --- |
| Topic not offered for the grade | `Error executing tool generate_problem: 'quadratics' is not offered for Class 7. Topics for Class 7: linear_equations, fractions, percentages.` |
| Answer contains no number | `Error executing tool check_answer: I could not find a number in that answer. Expected format: a whole number, for example 7 or -3.` |
| Fraction with zero denominator | `Error executing tool check_answer: A fraction cannot have 0 as its denominator. Expected format: …` |
| Argument fails the schema (wrong type, out of range, bad pattern, empty) | `Error executing tool get_hint: 1 validation error for get_hintArguments` followed by `level` and `Input should be less than or equal to 3 [type=less_than_equal, input_value=5, input_type=int]` |
| Unknown topic | `… topic  Input should be 'linear_equations', 'fractions', 'percentages' or 'quadratics' [type=literal_error, …]` |
| Invalid problem ID, such as `../etc/passwd` | `… problem_id  String should match pattern '^(lin\|frac\|pct\|quad)-g([6-9]\|10)-(easy\|medium\|hard)-(\d{1,6})$' [type=string_pattern_mismatch, …]` |

Schema validation runs **before** the tool's code. An invalid argument never reaches the maths layer.

### Protocol errors (JSON-RPC `error`)

The request itself is rejected, and the response has an `error` object instead of a `result`. The Python client raises `MCPError`.

| Code | Name | When |
| --- | --- | --- |
| `-32602` | Invalid params | Reading an unknown resource such as `syllabus://grade/12`, or invalid arguments to the `socratic_tutor` prompt. |
| `-32601` | Method not found | Calling a method the server does not implement. |

Full request and response pairs are in the [JSON-RPC examples](./json-rpc-examples.mdx).
