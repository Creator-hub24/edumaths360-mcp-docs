---
sidebar_position: 3
title: Configuration
description: How to start the server, its fixed limits, logging, and the host configuration format.
---

# Configuration

The server is designed to need **no configuration**: no API keys, no environment variables, no network access and no files on disk. This page lists everything you can control and every built-in limit.

## Starting the server

| Command | When to use it |
| --- | --- |
| `edumaths360-mcp` | The console script installed with the package. |
| `python -m edumaths360_mcp` | Same server, started through the Python module. Useful when you know the interpreter path but not the script path. |
| `uv --directory <path-to-server> run edumaths360-mcp` | From a host configuration. uv installs dependencies if needed. |

All three start the server on the **stdio** transport. The server does not open a network port.

## Requirements

| Item | Value |
| --- | --- |
| Python | 3.10 or later (CI uses 3.12) |
| Runtime dependency | `mcp>=2.3,<3` (the official MCP Python SDK) |
| Package name | `edumaths360-mcp`, version `0.1.0` |
| Server name / title | `edumaths360-practice` / `Edumaths360 Practice Server` |

## Built-in limits

These values are constants in the source code. They are not configurable at runtime, on purpose: a client should not be able to loosen them.

| Constant | Value | Defined in | Purpose |
| --- | --- | --- | --- |
| `REVEAL_AFTER_ATTEMPTS` | `3` | `server.py` | Wrong attempts before `check_answer` shows the worked solution. |
| `MAX_TRACKED_PROBLEMS` | `10000` | `server.py` | Maximum number of problems whose attempt counts are kept in memory. The oldest is forgotten first. |
| `MAX_HINT_LEVEL` | `3` | `problems.py` | Number of hint levels per problem. |
| `MAX_SEED` | `999999` | `problems.py` | Largest seed accepted by `generate_problem`. |
| `problem_id` max length | `32` | `server.py` | Maximum length of a problem ID argument. |
| `answer` length | `1` to `100` | `server.py` | Length limits for a student's answer. |

## State

The only state is the attempt counter used by `check_answer`. It lives in memory and is lost when the server stops. Each host starts its own server process, so two apps never share attempt counts. Problems themselves are not stored: the problem ID contains everything needed to rebuild the problem.

## Logging

The server logs to **stderr** at INFO level, in this format:

```text
%(asctime)s %(levelname)s %(name)s: %(message)s
```

Messages include `Starting Edumaths360 Practice Server 0.1.0 on stdio`, `generated lin-g8-medium-42` and `checked lin-g8-medium-42 attempt=1 correct=False`. Logs never contain answers or solutions. Hosts such as Claude Desktop capture stderr in their own log files.

:::danger Do not log to stdout
On the stdio transport, stdout carries JSON-RPC messages. Anything else written there breaks the connection. See [Troubleshooting](../troubleshooting.md#failed-to-parse-jsonrpc-message-from-server).
:::

## Host configuration format

Claude Desktop and Cursor use the same JSON structure:

```json
{
  "mcpServers": {
    "<display name>": {
      "command": "<program to run>",
      "args": ["<argument>", "..."],
      "env": {"<NAME>": "<value>"}
    }
  }
}
```

| Key | Required | Description |
| --- | --- | --- |
| `command` | Yes | The program to start, for example `uv` or a full path to `python`. |
| `args` | No | Arguments passed to the program. |
| `env` | No | Extra environment variables. This server does not read any. |

For file locations and examples, see [Configure Claude Desktop and Cursor](../how-to/configure-hosts.mdx).
