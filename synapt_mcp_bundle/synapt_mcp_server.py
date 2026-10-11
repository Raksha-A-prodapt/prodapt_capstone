"""Expose this project's Synapt query agent as a local Streamable HTTP MCP server."""
from __future__ import annotations

import json

from mcp.server.mcpserver import MCPServer

from query_agent import QueryAgent

server = MCPServer(
    name="synapt-query-bridge",
    version="1.0.0",
    instructions="Use these tools to query the configured Synapt knowledge provider.",
)


def _json_text(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, default=str)


@server.tool(description="Ask a question of the configured Synapt knowledge provider.")
async def ask_synapt(question: str, top_k: int = 5, graph_hops: int = 2) -> str:
    async with QueryAgent.from_env() as agent:
        return _json_text(await agent.ask(question, top_k=top_k, graph_hops=graph_hops))


@server.tool(description="Search concepts and entities in the Synapt knowledge graph.")
async def search_synapt(query: str, node_type: str | None = None, top_k: int = 10) -> str:
    async with QueryAgent.from_env() as agent:
        return _json_text(await agent.search(query, node_type=node_type, top_k=top_k))


@server.tool(description="Retrieve source text chunks relevant to a query.")
async def get_synapt_chunks(query: str, top_k: int = 5) -> str:
    async with QueryAgent.from_env() as agent:
        return _json_text(await agent.chunks(query, top_k=top_k))


@server.tool(description="Retrieve procedures relevant to an optional query.")
async def get_synapt_procedures(query: str | None = None) -> str:
    async with QueryAgent.from_env() as agent:
        return _json_text(await agent.procedures(query))


@server.tool(description="Get statistics for the configured Synapt provider.")
async def get_synapt_stats() -> str:
    async with QueryAgent.from_env() as agent:
        return _json_text(await agent.stats())


if __name__ == "__main__":
    server.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=8000,
        streamable_http_path="/mcp",
    )
