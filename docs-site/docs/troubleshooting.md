---
sidebar_position: 90
title: Troubleshooting
description: Real errors met while building and testing this server, with their causes and fixes.
---

# Troubleshooting

Every error on this page was actually hit while building, testing or documenting this project. The messages are copied from real output. If you meet an error that is not here, please [open an issue](https://github.com/Creator-hub24/edumaths360-mcp-docs/issues) with the full message.

## ModuleNotFoundError: No module named 'mcp.server.fastmcp'

**Full message:**

```text
ModuleNotFoundError: No module named 'mcp.server.fastmcp'. This is mcp 2.x, where FastMCP was renamed
to MCPServer (from mcp.server.mcpserver import MCPServer) and other APIs changed; see the migration guide
at https://py.sdk.modelcontextprotocol.io/v2/migration/#fastmcp-renamed-to-mcpserver or pin 'mcp<2' to
keep running v1 code.
```

**Cause:** You are following a tutorial written for version 1 of the MCP Python SDK, but version 2 is installed. Many blog posts and examples still use `from mcp.server.fastmcp import FastMCP`.

**Fix:** Use the version 2 import, as this project does:

```python
from mcp.server.mcpserver import MCPServer

mcp = MCPServer(name="my-server")
```

Other renamed imports you may need: `ToolError` and `ResourceNotFoundError` are in `mcp.server.mcpserver.exceptions`, and the client is `from mcp import Client`. If you must run old code unchanged, pin the old SDK with `pip install "mcp<2"`, but new projects should use version 2.

## Failed to parse JSONRPC message from server

**Full message (from the Python client):**

```text
Failed to parse JSONRPC message from server
...
pydantic_core._pydantic_core.ValidationError: 1 validation error for union[JSONRPCRequest,JSONRPCNotification,JSONRPCResponse,JSONRPCError]
  Invalid JSON: expected value at line 1 column 1 [type=json_invalid, input_value='adding 1 and 2', input_type=str]
```

**Cause:** The server wrote something that is not JSON to **stdout**. On the stdio transport, stdout is the protocol channel: every line must be a JSON-RPC message. Here, a tool contained a debugging line:

```python
print(f"adding {a} and {b}")  # breaks the protocol
```

The `input_value` in the message shows the exact text that was printed. Depending on the client, the stray line is skipped (the Python SDK logs this error and carries on) or the connection fails. Either way, it is a bug.

**Fix:** Send debugging output to **stderr**, ideally through `logging`:

```python
import logging
import sys

logging.basicConfig(stream=sys.stderr, level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("adding %s and %s", a, b)  # safe: goes to stderr
```

Hosts such as Claude Desktop save a server's stderr in their log files, so you do not lose the output. This project's server logs only to stderr; see [Configuration](./reference/configuration.md).

## Prompt errors show as "Internal server error" (-32603)

**Symptom:** Calling the `socratic_tutor` prompt with a bad topic returned a generic JSON-RPC error `-32603` with the message `Internal server error`, which hides the real reason from the user.

**Cause:** An early version raised a plain `ValueError` in the prompt function. The SDK treats unexpected exceptions in prompts as internal errors.

**Fix:** Raise `MCPError` with the `INVALID_PARAMS` code, which is what the current server does:

```python
from mcp import MCPError
from mcp.types import INVALID_PARAMS

raise MCPError(INVALID_PARAMS, f"Unknown topic '{topic}'. Choose one of: {', '.join(TOPICS)}.")
```

The client now receives `-32602 Unknown topic 'algebra'. Choose one of: linear_equations, fractions, percentages, quadratics.`

## Tool descriptions contain odd spaces and line breaks

**Symptom:** In the Inspector, tool descriptions had extra indentation and broken lines.

**Cause:** The description came from a multi-line docstring, and the indentation inside the docstring was sent to the client as part of the text.

**Fix:** Pass an explicit `description=` string to the `@mcp.tool()` decorator, as the server does. This also lets you write descriptions for the model (when to call the tool and what it returns) separately from code comments for developers.

## "1 validation error for get_hintArguments"

**Full message:**

```text
Error executing tool get_hint: 1 validation error for get_hintArguments
level
  Input should be less than or equal to 3 [type=less_than_equal, input_value=5, input_type=int]
```

**Cause:** This is the server working as intended. The argument broke the tool's JSON Schema (here, hint `level` 5 when the maximum is 3). The SDK validates arguments before running the tool and returns the result with `isError: true`.

**Fix:** Correct the argument. The second line names the argument and the third explains the rule. The [Tools reference](./reference/tools.md#errors) lists every limit.

## "`Worksheet` is not fully defined"

**Full message (shortened):**

```text
`Worksheet` is not fully defined; you should define `WorksheetItem`, then call `Worksheet.model_rebuild()`.
```

**Cause:** This came up while testing the [Add a tool](./how-to/add-a-tool.mdx) example. The file used `from __future__ import annotations` and was loaded with `importlib` without being registered in `sys.modules`. With that import, type hints are stored as strings, and Pydantic could not find the `WorksheetItem` class to resolve them.

**Fix:** Remove `from __future__ import annotations` from modules that define Pydantic models used as tool outputs (Python 3.10+ supports `list[WorksheetItem]` and `X | None` without it), or import the module normally.

## `npx @modelcontextprotocol/inspector` starts an old version

**Symptom:** The Inspector printed a deprecation notice or behaved differently from these docs.

**Cause:** `npx` reused an old cached copy (version 0.15) instead of downloading the latest.

**Fix:** Ask for the latest version explicitly:

```bash
npx @modelcontextprotocol/inspector@latest
```

The latest Inspector declares Node.js 22.19 or later. On Node.js 20 it printed `EBADENGINE` warnings during install; upgrade Node.js to 22 to avoid them.

## Not listed here?

If Claude Desktop does not show the server at all, work through the restart and verification steps in [Connect to Claude Desktop](./tutorials/connect-claude-desktop.mdx), then read the host's log file. If you hit a new error, please [open an issue](https://github.com/Creator-hub24/edumaths360-mcp-docs/issues) with the full message so it can be added here.
