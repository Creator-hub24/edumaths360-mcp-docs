"""Capture real JSON-RPC traffic from the Edumaths360 Practice Server.

Starts the server as a subprocess, speaks raw newline-delimited JSON-RPC over
its stdin/stdout (exactly what an MCP host does), and writes every
request/response pair to example_payloads.json. No SDK client is used, so
the file shows the wire format byte for byte.

Usage:
    python snippets/capture_payloads.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

OUT = Path(__file__).with_name("example_payloads.json")
PROTOCOL_VERSION = "2025-11-25"  # handshake-era version that current desktop hosts negotiate


def main() -> None:
    proc = subprocess.Popen(
        [sys.executable, "-m", "edumaths360_mcp"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        encoding="utf-8",
    )
    assert proc.stdin and proc.stdout
    next_id = 0
    log: list[dict] = []

    def send(method: str, params: dict | None = None, *, title: str, notify: bool = False) -> dict | None:
        nonlocal next_id
        message: dict = {"jsonrpc": "2.0", "method": method}
        if not notify:
            next_id += 1
            message["id"] = next_id
        if params is not None:
            message["params"] = params
        proc.stdin.write(json.dumps(message) + "\n")
        proc.stdin.flush()
        if notify:
            log.append({"title": title, "request": message, "response": None})
            return None
        response = json.loads(proc.stdout.readline())
        log.append({"title": title, "request": message, "response": response})
        return response

    send(
        "initialize",
        {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": {"name": "capture-script", "version": "1.0"},
        },
        title="1. Handshake: initialize",
    )
    send(
        "notifications/initialized",
        title="2. Handshake: initialized notification",
        notify=True,
    )
    send("tools/list", {}, title="3. Discover tools")
    send(
        "tools/call",
        {
            "name": "generate_problem",
            "arguments": {
                "topic": "linear_equations",
                "grade": 8,
                "difficulty": "medium",
                "seed": 42,
            },
        },
        title="4. Generate a problem",
    )
    send(
        "tools/call",
        {
            "name": "check_answer",
            "arguments": {"problem_id": "lin-g8-medium-42", "answer": "x = -14"},
        },
        title="5. Check a wrong answer (sign error)",
    )
    send(
        "tools/call",
        {
            "name": "get_hint",
            "arguments": {"problem_id": "lin-g8-medium-42", "level": 2},
        },
        title="6. Ask for a level 2 hint",
    )
    send(
        "tools/call",
        {
            "name": "check_answer",
            "arguments": {"problem_id": "lin-g8-medium-42", "answer": "14"},
        },
        title="7. Check the correct answer",
    )
    send(
        "tools/call",
        {"name": "generate_problem", "arguments": {"topic": "quadratics", "grade": 7}},
        title="8. Tool error: topic not offered for the grade",
    )
    send("resources/list", {}, title="9. List static resources")
    send("resources/templates/list", {}, title="10. List resource templates")
    send("resources/read", {"uri": "syllabus://grade/9"}, title="11. Read a resource")
    send("prompts/list", {}, title="12. List prompts")
    send(
        "prompts/get",
        {"name": "socratic_tutor", "arguments": {"topic": "fractions", "grade": "7"}},
        title="13. Get a prompt",
    )
    send("resources/read", {"uri": "syllabus://grade/12"}, title="14. Protocol error: resource not found")
    send("tools/unknown_method", {}, title="15. Protocol error: unknown method")

    proc.stdin.close()
    proc.wait(timeout=10)

    OUT.write_text(
        json.dumps(
            {
                "description": (
                    "Real JSON-RPC 2.0 messages exchanged with the Edumaths360 Practice Server over stdio, "
                    "captured by snippets/capture_payloads.py. Regenerate with: python snippets/capture_payloads.py"
                ),
                "protocolVersion": PROTOCOL_VERSION,
                "exchanges": log,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(log)} exchanges to {OUT}")


if __name__ == "__main__":
    main()
