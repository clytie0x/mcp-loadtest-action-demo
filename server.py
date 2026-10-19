#!/usr/bin/env python3
"""A tiny MCP server over stdio, standard library only.

    python3 server.py              healthy: answers every call
    python3 server.py --deadlock   every tools/call waits for a lazy
                                   initialization that never finishes

The second mode reproduces a common lazy-initialization deadlock: the server
answers initialize and tools/list fine, then hangs on the first tool call.
"""

import json
import sys
import threading

DEADLOCK = "--deadlock" in sys.argv[1:]
initialized = threading.Event()  # set once lazy initialization finishes
write_lock = threading.Lock()

TOOLS = [
    {
        "name": "get_status",
        "description": "Report that the server is up.",
        "inputSchema": {"type": "object", "properties": {}},
        "annotations": {"readOnlyHint": True, "destructiveHint": False},
    },
    {
        "name": "add",
        "description": "Add two numbers.",
        "inputSchema": {
            "type": "object",
            "properties": {"a": {"type": "number"}, "b": {"type": "number"}},
            "required": ["a", "b"],
        },
        "annotations": {"readOnlyHint": True},
    },
]


def send(message):
    with write_lock:
        sys.stdout.write(json.dumps(message) + "\n")
        sys.stdout.flush()


def call_tool(request_id, params):
    if DEADLOCK:
        initialized.wait()  # the bug: nothing ever sets it
    name = params.get("name")
    args = params.get("arguments") or {}
    if name == "get_status":
        text = "ok"
    elif name == "add":
        text = str(args["a"] + args["b"])
    else:
        send({"jsonrpc": "2.0", "id": request_id,
              "error": {"code": -32602, "message": f"unknown tool {name}"}})
        return
    send({"jsonrpc": "2.0", "id": request_id,
          "result": {"content": [{"type": "text", "text": text}]}})


def main():
    for line in sys.stdin:
        if not line.strip():
            continue
        message = json.loads(line)
        method, request_id = message.get("method"), message.get("id")
        if request_id is None:
            continue  # notifications need no answer
        params = message.get("params") or {}
        if method == "initialize":
            send({"jsonrpc": "2.0", "id": request_id, "result": {
                "protocolVersion": params.get("protocolVersion", "2025-06-18"),
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "demo", "version": "1.0.0"},
            }})
        elif method == "tools/list":
            send({"jsonrpc": "2.0", "id": request_id, "result": {"tools": TOOLS}})
        elif method == "tools/call":
            threading.Thread(target=call_tool, args=(request_id, params), daemon=True).start()
        elif method == "ping":
            send({"jsonrpc": "2.0", "id": request_id, "result": {}})
        else:
            send({"jsonrpc": "2.0", "id": request_id,
                  "error": {"code": -32601, "message": f"method not found: {method}"}})


if __name__ == "__main__":
    main()
