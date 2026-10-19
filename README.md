# mcp-loadtest Action demo

Checks the [mcp-loadtest](https://github.com/clytie0x/mcp-loadtest) GitHub
Action end to end, pinned to `v0.4.0`.

`server.py` is a small MCP server with no dependencies. The
[workflow](.github/workflows/demo.yml) probes it twice:

| Job | Server | Expected |
|---|---|---|
| healthy server passes | `python3 server.py` | the Action passes |
| deadlocking server fails | `python3 server.py --deadlock` | the Action fails with deadlocks, and the job checks that it did |

Neither job names a tool. Without `--tool`, `deadlock-probe` probes the first
tool the server marks read-only that takes no required arguments, here
`get_status`.

Run the same probe locally with a
[release binary](https://github.com/clytie0x/mcp-loadtest/releases/tag/v0.4.0):

```bash
mcp-loadtest deadlock-probe --server "python3 server.py"
mcp-loadtest deadlock-probe --server "python3 server.py --deadlock"
```
