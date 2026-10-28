---
sidebar_position: 2
title: Resources and prompts
description: Reference for the syllabus resources and the socratic_tutor prompt.
---

# Resources and prompts

**Resources** are read-only data that a host can load into the model's context. **Prompts** are reusable message templates that a user picks, for example from a menu in Claude Desktop. Both are optional MCP features; this server provides two resources and one prompt.

## Resources

Both resources return JSON with the MIME type `application/json`.

### `syllabus://topics`

| Property | Value |
| --- | --- |
| Name | `all_topics` |
| Title | All topics |
| Description | Every topic the server can generate, with the grades it is offered for. |

**Response text:**

```json
{
  "topics": [
    {
      "topic": "linear_equations",
      "description": "Solve equations in one variable, from x + b = c up to brackets on both sides.",
      "grades": [6, 7, 8, 9, 10]
    },
    {
      "topic": "fractions",
      "description": "Add, subtract and divide fractions, and give answers in simplest form.",
      "grades": [6, 7, 8]
    },
    {
      "topic": "percentages",
      "description": "Percentage of an amount, percentage increase/decrease, and reverse percentages.",
      "grades": [6, 7, 8, 9, 10]
    },
    {
      "topic": "quadratics",
      "description": "Solve quadratic equations by factorisation.",
      "grades": [9, 10]
    }
  ]
}
```

### `syllabus://grade/{grade}`

A *resource template*: `{grade}` is a parameter the client fills in.

| Property | Value |
| --- | --- |
| Name | `grade_syllabus` |
| Title | Syllabus for one grade |
| Description | Topics and difficulty levels available for a Class 6-10 grade. |
| Parameter | `grade`: a whole number from 6 to 10 |

**Example:** `syllabus://grade/9`

```json
{
  "grade": 9,
  "topics": [
    {
      "topic": "linear_equations",
      "description": "Solve equations in one variable, from x + b = c up to brackets on both sides.",
      "difficulties": ["easy", "medium", "hard"]
    },
    {
      "topic": "percentages",
      "description": "Percentage of an amount, percentage increase/decrease, and reverse percentages.",
      "difficulties": ["easy", "medium", "hard"]
    },
    {
      "topic": "quadratics",
      "description": "Solve quadratic equations by factorisation.",
      "difficulties": ["easy", "medium", "hard"]
    }
  ]
}
```

**Errors:** any other value, such as `12` or `abc`, returns JSON-RPC error `-32602` with the message `No syllabus for grade '12'. Use a grade from 6 to 10.` The SDK also rejects parameter values that look like path traversal (for example `..`) by default.

## Prompts

### `socratic_tutor`

| Property | Value |
| --- | --- |
| Title | Socratic maths tutor |
| Description | Run a practice session where the assistant asks guiding questions instead of giving answers. |

**Arguments** (both optional strings; MCP prompt arguments are always strings):

| Name | Default | Allowed values |
| --- | --- | --- |
| `topic` | `linear_equations` | One of the four topic names. |
| `grade` | `8` | A grade the topic is offered for, as a string, for example `"7"`. |

**Result:** one `user` message. For `topic="fractions"` and `grade="7"`:

```text
You are a patient maths tutor for a Class 7 student practising fractions.

Rules:
1. Call generate_problem with topic='fractions' and grade=7, then show the student the statement.
2. Never solve the problem for the student and never state the final answer yourself.
3. Ask one short guiding question at a time, for example 'What operation undoes + 7?'.
4. When the student gives an answer, call check_answer and share the feedback in your own words.
5. If the student is stuck, call get_hint starting at level 1. Only go to the next level if they are still stuck after trying.
6. Praise effort and method, not only correct answers.

Start by greeting the student and generating the first problem.
```

**Errors** (JSON-RPC `-32602`, raised as `MCPError` in the Python client):

| Input | Message |
| --- | --- |
| `topic="ignore previous instructions"` | `Unknown topic 'ignore previous instructions'. Choose one of: linear_equations, fractions, percentages, quadratics.` |
| `topic="quadratics", grade="7"` | `'quadratics' is offered for grades [9, 10]; got '7'.` |

The arguments are checked against fixed lists before they are inserted into the prompt text. This stops a client from injecting its own instructions through a prompt argument. See [Security model](../explanation/security-model.md#1-input-validation).
