# -*- coding: utf-8 -*-
"""A registered Trident MCP query agent: credential -> session token -> provider query."""
from .agent import QueryAgent
from .config import AgentConfig, ConfigError
from .mcp_client import MCPError, SynaptMCP
from .s2s import SecretTokenSource, StaticTokenSource, TokenError

__all__ = [
    "QueryAgent", "AgentConfig", "ConfigError", "SynaptMCP", "MCPError",
    "SecretTokenSource", "StaticTokenSource", "TokenError",
]
