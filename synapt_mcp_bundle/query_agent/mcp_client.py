# -*- coding: utf-8 -*-
"""MCP transport to the Synapt context provider, authorised by an S2S token.

One long-lived streamable-HTTP session is opened and reused across calls. The
bearer token comes from the agent's registered identity, so every call to the
substrate is attributable to this agent in the registry.
"""
from __future__ import annotations

import json
from contextlib import AsyncExitStack
from typing import Any

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from .s2s import SecretTokenSource, StaticTokenSource


class MCPError(RuntimeError):
    """Transport failure, or a tool that reported an error."""


class SynaptMCP:
    def __init__(
        self,
        *,
        mcp_url: str,
        provider_id: str,
        token_source: "SecretTokenSource | StaticTokenSource",
        verify: bool | str = True,
        timeout: float = 120.0,
    ) -> None:
        # Use the URL verbatim. The registered-agent endpoint (/api/mcp) 307-
        # redirects if a trailing slash is added, so DON'T normalise it - the
        # env value is authoritative.
        self.mcp_url = mcp_url
        self.provider_id = provider_id
        self.tokens = token_source
        self._verify = verify
        self._timeout = timeout
        self._stack: AsyncExitStack | None = None
        self._session: ClientSession | None = None

    async def __aenter__(self) -> "SynaptMCP":
        await self.connect()
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        if self._stack is not None:
            await self._stack.aclose()
            self._stack = None
            self._session = None

    @staticmethod
    def _flatten(exc: BaseException, depth: int = 0) -> str:
        """Render an anyio ExceptionGroup down to its actual causes.

        The MCP transport runs its reads and writes in a task group, so a plain
        401 arrives wrapped in a BaseExceptionGroup whose str() is just
        "unhandled errors in a TaskGroup" - useless on its own.
        """
        subs = getattr(exc, "exceptions", None)
        if subs and depth < 4:
            inner = "; ".join(SynaptMCP._flatten(e, depth + 1) for e in subs)
            return inner or f"{type(exc).__name__}"
        text = str(exc).strip()
        return f"{type(exc).__name__}: {text}" if text else type(exc).__name__

    async def _diagnose(self, token: str) -> str:
        """Ask the endpoint directly what it thinks of this token.

        The MCP transport does its real HTTP inside a task group, so an auth
        failure reaches us as a bare CancelledError with the status code lost.
        One plain POST recovers it, and only runs when something already failed.
        """
        body = {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {"name": "synapt-query-agent", "version": "1.0"},
            },
        }
        try:
            async with httpx.AsyncClient(timeout=20, verify=self._verify) as http:
                resp = await http.post(
                    self.mcp_url,
                    json=body,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Accept": "application/json, text/event-stream",
                    },
                )
        except Exception as exc:  # network-level; nothing more to add
            return f"probe failed: {type(exc).__name__}: {exc}"
        return f"HTTP {resp.status_code}: {resp.text[:300].strip()}"

    async def connect(self, *, force_token: bool = False) -> None:
        await self.aclose()
        token = await self.tokens.token(force=force_token)
        verify = self._verify

        stack = AsyncExitStack()
        try:
            http_client = httpx.AsyncClient(
                headers={"Authorization": f"Bearer {token}"},
                timeout=self._timeout,
                verify=verify,
            )
            await stack.enter_async_context(http_client)
            read, write = await stack.enter_async_context(
                streamable_http_client(
                    self.mcp_url,
                    http_client=http_client,
                )
            )
            session = await stack.enter_async_context(ClientSession(read, write))
            await session.initialize()
        except BaseException as exc:
            try:
                await stack.aclose()
            except BaseException:
                # A failed handshake often also fails to unwind cleanly; the
                # original cause is what matters, so don't let teardown mask it.
                pass
            detail = self._flatten(exc)
            # The wrapped error is usually uninformative; ask the server itself.
            probe = await self._diagnose(token)
            detail = f"{detail} | server said: {probe}"
            hint = ""
            if "401" in detail or "invalid_token" in detail or "Unauthorized" in detail:
                hint = (
                    " - the access token was rejected. Check the token is current and "
                    "that its audience covers this endpoint."
                )
            elif "403" in detail or "RBAC" in detail:
                hint = " - 403 usually means a tool/provider your grant does not cover."
            elif "307" in detail:
                hint = (
                    " - a 307 redirect means the URL has a trailing slash it should not: "
                    "the /api/mcp endpoint must be used without one."
                )
            raise MCPError(f"could not open MCP session at {self.mcp_url}{hint} [{detail}]") from exc
        self._stack = stack
        self._session = session

    async def list_tools(self) -> list[dict]:
        if self._session is None:
            await self.connect()
        assert self._session is not None
        result = await self._session.list_tools()
        return [
            {"name": t.name, "description": t.description, "schema": t.input_schema}
            for t in result.tools
        ]

    # ── payload handling ─────────────────────────────────────────────────
    @staticmethod
    def _sanitize(text: str) -> str:
        """Drop the control characters the server rejects inside JSON strings."""
        text = text.replace("\r\n", " ").replace("\r", " ").replace("\n", " ")
        return "".join(
            ch if (ord(ch) >= 0x20 and ord(ch) != 0x7F) or ch == "\t" else " " for ch in text
        )

    @staticmethod
    def _decode(value: Any) -> Any:
        """Undo double-encoding: these tools return JSON *as a string*."""
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return value

    @classmethod
    def _unwrap(cls, result: Any) -> Any:
        structured = getattr(result, "structuredContent", None)
        if structured:
            # FastMCP wraps bare returns under "result", and that value is
            # itself a JSON string - so this needs unwrapping twice.
            if isinstance(structured, dict) and set(structured) == {"result"}:
                return cls._decode(structured["result"])
            return structured
        texts = [
            b.text
            for b in (getattr(result, "content", None) or [])
            if getattr(b, "type", None) == "text"
        ]
        return cls._decode("\n".join(texts)) if texts else None

    async def call_tool(self, tool: str, *, sanitize: bool = True, **args: Any) -> Any:
        """Call an MCP tool with provider_id injected. Retries once on auth failure."""
        if self._session is None:
            await self.connect()
        assert self._session is not None

        clean = {
            k: (self._sanitize(v) if sanitize and isinstance(v, str) else v)
            for k, v in args.items()
            if v is not None
        }
        clean["provider_id"] = self.provider_id

        try:
            result = await self._session.call_tool(tool, clean)
        except BaseException as exc:
            # An expired token can surface as an opaque transport error rather
            # than a clean 401 (the 401 happens inside the transport's own
            # background write task), so assume staleness and rebuild once.
            await self.connect(force_token=True)
            assert self._session is not None
            try:
                result = await self._session.call_tool(tool, clean)
            except BaseException as retry_exc:
                raise MCPError(
                    f"tool {tool} failed after a token refresh: {self._flatten(retry_exc)}"
                ) from exc

        if getattr(result, "isError", False):
            raise MCPError(f"tool {tool} reported an error: {self._unwrap(result)}")
        return self._unwrap(result)
