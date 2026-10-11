# Synapt MCP workspace bundle

This folder is a copy of the Synapt MCP bridge runtime. Open this folder in
VS Code (or add it as a workspace folder) to load the MCP server configuration
from `.vscode/mcp.json`.

## Install and start

Run these commands from this folder in Command Prompt:

```cmd
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
set SYNAPT_VERIFY_SSL=false
.venv\Scripts\python.exe synapt_mcp_server.py
```

Keep the terminal open while VS Code Chat uses the server. The MCP endpoint is
`http://127.0.0.1:8000/mcp`; the included MCP configuration points to it.
In VS Code, open the MCP servers view and start or restart `synapt` if it is
not connected automatically.
Only one process can listen on port 8000 at a time. If the port is already in
use, use the server already running or stop that server before starting this
copy.

The bridge reads credentials from this folder's `.env`. This bundle's `.env`
is a local copy, ignored by Git. Do not share it or commit it. The
`SYNAPT_VERIFY_SSL=false` setting disables TLS certificate checks for the
outgoing Synapt connection and is insecure; use a trusted CA bundle instead
for routine use.

The server binds to localhost and has no separate client authentication. Do
not expose it to other computers or bind it to `0.0.0.0`.
