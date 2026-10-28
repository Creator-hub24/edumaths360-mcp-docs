---
sidebar_position: 4
title: Debug with the MCP Inspector
description: Use the MCP Inspector's web UI and command-line mode to test tools, resources and prompts without an AI app.
---

# Debug with the MCP Inspector

The [MCP Inspector](https://github.com/modelcontextprotocol/inspector) is the official developer tool for MCP servers. It acts as an MCP client, so you can call your server directly and see the raw responses, without an AI model guessing what to do.

Use it when:

- a host such as Claude Desktop does not show your tools,
- a tool returns something unexpected,
- you want to check a schema or an error message before you write documentation.

**Requirements:** Node.js 22 or later (the Inspector is run with `npx`, so there is nothing to install). Run the commands from the repository root after `uv sync --extra dev` in `server/`.

## Option 1: The web UI

```bash
npx @modelcontextprotocol/inspector uv --directory server run edumaths360-mcp
```

The Inspector starts the server and prints a local URL. Open it in your browser. The layout differs slightly between Inspector versions, but the workflow is the same:

1. Connect to the server. The server name and version appear.
2. Open the **Tools** view and list the tools. Select `generate_problem`, fill in `topic` and `grade`, and run it.
3. Copy the `problem_id` from the result, then run `check_answer` with a wrong answer to see the feedback.
4. Open the **Resources** and **Prompts** views to read `syllabus://topics` or render `socratic_tutor`.
5. Check the Inspector's history and notifications panes to see each request and response.

## Option 2: The command line

The `--cli` flag sends one request and prints the JSON response. It is ideal for quick checks and scripts.

**List tools:**

```bash
npx @modelcontextprotocol/inspector --cli uv --directory server run edumaths360-mcp --method tools/list
```

**Call a tool:**

```bash
npx @modelcontextprotocol/inspector --cli uv --directory server run edumaths360-mcp \
  --method tools/call --tool-name get_hint \
  --tool-arg problem_id=lin-g8-medium-42 --tool-arg level=1
```

```json
{
  "content": [
    {
      "type": "text",
      "text": "{\n  \"problem_id\": \"lin-g8-medium-42\",\n  \"level\": 1,\n  \"max_level\": 3,\n  \"hint\": \"Undo the operations in reverse order: deal with the number added or subtracted first, then the multiplication.\",\n  \"next_step\": \"Try the problem again. If still stuck, ask for level 2.\"\n}"
    }
  ],
  "structuredContent": {
    "problem_id": "lin-g8-medium-42",
    "level": 1,
    "max_level": 3,
    "hint": "Undo the operations in reverse order: deal with the number added or subtracted first, then the multiplication.",
    "next_step": "Try the problem again. If still stuck, ask for level 2."
  },
  "isError": false
}
```

**Read a resource:**

```bash
npx @modelcontextprotocol/inspector --cli uv --directory server run edumaths360-mcp \
  --method resources/read --uri syllabus://topics
```

**Render a prompt:**

```bash
npx @modelcontextprotocol/inspector --cli uv --directory server run edumaths360-mcp \
  --method prompts/get --prompt-name socratic_tutor --prompt-args topic=fractions grade=7
```

## Reading what you see

| You see | It means | Next step |
| --- | --- | --- |
| `"isError": true` with a message | The tool ran (or its input validation ran) and reported a problem. | Read the message; it says which argument is wrong. See [tool errors](../reference/tools.md#errors). |
| `{"error":{"code":"tool_is_error", ...}}` from `--cli` | The Inspector CLI's summary when a tool returns `isError: true`. | Run the same call in the web UI to see the full result. |
| A JSON-RPC `error` with a code such as `-32602` | A protocol-level error, for example an unknown resource URI. | See the [JSON-RPC examples](../reference/json-rpc-examples.mdx). |
| The Inspector cannot connect | The server failed to start or wrote something that is not JSON-RPC to stdout. | Run the command on its own and read the stderr output. See [Troubleshooting](../troubleshooting.md). |

## Tips

- **Reproducible problems.** Pass `--tool-arg seed=42` to `generate_problem` to get the same problem every time. The `problem_id` then works as a stable test fixture.
- **Use the same command as your host.** If Claude Desktop runs `uv --directory ... run edumaths360-mcp`, debug with exactly that command. Many "works in the terminal, fails in the app" problems come from a different interpreter or path.
- **Logs go to stderr.** The server logs each generated and checked problem at INFO level. Those lines never mix with the protocol messages on stdout.
