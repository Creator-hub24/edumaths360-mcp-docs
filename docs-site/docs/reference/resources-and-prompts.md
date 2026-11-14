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
| Description | Every topic the server can generate, grouped by exam section (quant, reasoning or varc). |

**Response text** (shortened: the real response lists all 13 topics, and `difficulties` is spread over several lines):

```json
{
  "topics": [
    {
      "topic": "percentages",
      "section": "quant",
      "area": "arithmetic",
      "description": "Percentage of a quantity, successive percentage change, and price-consumption problems.",
      "difficulties": ["easy", "medium", "hard"]
    },
    {
      "topic": "profit_loss",
      "section": "quant",
      "area": "arithmetic",
      "description": "Cost price, selling price, marked price and discount, and profit or loss percentages.",
      "difficulties": ["easy", "medium", "hard"]
    },
    …
    {
      "topic": "number_series",
      "section": "reasoning",
      "area": "logical reasoning",
      "description": "Find the next term: arithmetic, geometric, difference and mixed series.",
      "difficulties": ["easy", "medium", "hard"]
    }
  ]
}
```

| `section` | `area` | Topics |
| --- | --- | --- |
| `quant` | `arithmetic` | `percentages`, `profit_loss`, `ratio_proportion`, `time_speed_distance`, `time_work`, `interest` |
| `quant` | `algebra` | `linear_equations`, `quadratics` |
| `quant` | `number system` | `number_system` |
| `reasoning` | `logical reasoning` | `number_series` |
| `varc` | `verbal ability` | `para_jumbles`, `odd_sentence_out`, `para_summary` |

### `syllabus://section/{section}`

A *resource template*: `{section}` is a parameter the client fills in.

| Property | Value |
| --- | --- |
| Name | `section_syllabus` |
| Title | Syllabus for one exam section |
| Description | Topics and difficulty levels in one section: 'quant', 'reasoning' or 'varc'. |
| Parameter | `section`: `quant`, `reasoning` or `varc` |

**Example:** `syllabus://section/reasoning`

```json
{
  "section": "reasoning",
  "description": "Logical reasoning: pattern-based items with one verifiable numeric answer.",
  "topics": [
    {
      "topic": "number_series",
      "section": "reasoning",
      "area": "logical reasoning",
      "description": "Find the next term: arithmetic, geometric, difference and mixed series.",
      "difficulties": ["easy", "medium", "hard"]
    }
  ]
}
```

`syllabus://section/quant` returns the nine quant topics in the same shape, with the description `Quantitative aptitude: arithmetic, algebra and number system.` `syllabus://section/varc` returns `para_jumbles`, `odd_sentence_out` and `para_summary` (area `verbal ability`) with the description `Verbal ability (VARC): para jumbles, odd sentence out and para summary, on original passages.`

**Errors:** any other value, such as `gk`, returns JSON-RPC error `-32602` with the message `No syllabus for section 'gk'. Use one of: quant, reasoning, varc.` The SDK also rejects parameter values that look like path traversal (for example `..`) by default.

## Prompts

### `socratic_tutor`

| Property | Value |
| --- | --- |
| Title | Socratic CAT tutor |
| Description | Run a CAT-style practice session where the assistant asks guiding questions instead of giving answers. |

**Arguments** (both optional strings; MCP prompt arguments are always strings):

| Name | Default | Allowed values |
| --- | --- | --- |
| `topic` | `percentages` | One of the 13 topic names, for example `time_work`. |
| `difficulty` | `medium` | `easy`, `medium` or `hard`. |

**Result:** one `user` message. For `topic="time_work"` and `difficulty="hard"`:

```text
You are a patient quantitative aptitude and reasoning coach for a CAT/MBA aspirant practising time and work at hard difficulty.

Rules:
1. Call generate_problem with topic='time_work' and difficulty='hard', then show the student the statement.
2. Never solve the problem for the student and never state the final answer yourself.
3. Ask one short guiding question at a time, for example 'What is the cost price here?'.
4. When the student gives an answer, call check_answer and share the feedback in your own words.
5. If the student is stuck, call get_hint starting at level 1. Only go to the next level if they are still stuck after trying.
6. Praise method and reasoning, not only correct answers. Once they are correct, ask whether a faster approach (a shortcut or an elimination trick) would also work, as it would in the exam.

Start by greeting the student and generating the first problem.
```

For a VARC topic such as `para_summary`, the first line names a `verbal ability (VARC) coach` instead, and the example question in rule 3 becomes `'Which sentence introduces the topic?'`. The other rules are the same.

**Errors** (JSON-RPC `-32602`, raised as `MCPError` in the Python client):

| Input | Message |
| --- | --- |
| `topic="ignore previous instructions"` | `Unknown topic 'ignore previous instructions'. Choose one of: percentages, profit_loss, ratio_proportion, time_speed_distance, time_work, interest, linear_equations, quadratics, number_system, number_series, para_jumbles, odd_sentence_out, para_summary.` |
| `topic="time_work", difficulty="insane"` | `Unknown difficulty 'insane'. Choose one of: easy, medium, hard.` |

The arguments are checked against fixed lists before they are inserted into the prompt text. This stops a client from injecting its own instructions through a prompt argument. See [Security model](../explanation/security-model.md#1-input-validation).
