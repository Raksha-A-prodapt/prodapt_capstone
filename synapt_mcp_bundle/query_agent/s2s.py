# -*- coding: utf-8 -*-
"""Session-token sources for the Trident MCP registered-agent flow.

Two ways to obtain the Bearer token the MCP endpoint requires:

* `SecretTokenSource` - the registered-agent flow: POST client_id + client_secret
  to ``/generate_token`` and cache the session token that comes back.
* `StaticTokenSource` - a session token pasted in directly (it expires).

Both expose the same ``token(force=...)`` coroutine so the MCP client cannot
tell them apart.
"""
from __future__ import annotations

import base64
import json
import time
from typing import Any

import httpx


class TokenError(RuntimeError):
    """The token endpoint failed, or a static token cannot be refreshed."""


def decode_exp(token: str) -> float:
    """Read `exp` out of a JWT without verifying it."""
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        return float(json.loads(base64.urlsafe_b64decode(payload)).get("exp", 0))
    except Exception:
        return 0.0


class StaticTokenSource:
    """A session token minted elsewhere (e.g. the guide's curl) and pasted in.

    Cannot refresh, so `force=True` raises rather than silently handing back the
    same expired token and failing again one layer up.
    """

    def __init__(self, token: str, *, client_id: str = "(static token)") -> None:
        if not token:
            raise TokenError("StaticTokenSource needs a non-empty token")
        self.client_id = client_id
        self.scope: Any = None
        self._token = token

    async def token(self, *, force: bool = False) -> str:
        if force:
            raise TokenError(
                "the session token was rejected and SYNAPT_AGENT_TOKEN cannot be "
                "refreshed - paste a fresh token, or switch to the registered-agent "
                "flow by setting SYNAPT_AGENT_CLIENT_ID + SYNAPT_AGENT_CLIENT_SECRET."
            )
        return self._token


class SecretTokenSource:
    """Registered-agent flow: exchange client_id + client_secret for a session token.

    Per the Trident MCP "Registered Agent Integration Guide": POST the two
    credentials as JSON to ``<mcp base>/generate_token`` and present the returned
    ``token`` as a Bearer credential on every tool call. The body is exactly
    ``{"client_id", "client_secret"}`` - the guide is explicit that nothing else
    (no grant_type, no scope, no subject_token) belongs in this request; the
    grant/scope is fixed server-side and echoed back in the response.

    The response also carries ``scope`` (which tools on which providers this
    token may call) and ``expires_at`` (ISO-8601, UTC); both are captured.
    """

    def __init__(
        self,
        *,
        token_url: str,
        client_id: str,
        client_secret: str,
        verify: bool | str = True,
        timeout: float = 30.0,
    ) -> None:
        if not (token_url and client_id and client_secret):
            raise TokenError("token_url, client_id and client_secret are all required")
        self.token_url = token_url
        self.client_id = client_id
        self._secret = client_secret
        self._verify = verify
        self._timeout = timeout
        self._token: str | None = None
        self._expiry = 0.0
        self.scope: Any = None  # last grant echoed back by the token endpoint

    async def token(self, *, force: bool = False) -> str:
        if not force and self._token and time.time() < self._expiry - 30:
            return self._token

        async with httpx.AsyncClient(timeout=self._timeout, verify=self._verify) as http:
            resp = await http.post(
                self.token_url,
                json={"client_id": self.client_id, "client_secret": self._secret},
            )
        if resp.status_code == 401:
            raise TokenError(
                f"/generate_token returned 401 for client {self.client_id!r}: the "
                f"client_id/client_secret is wrong or the credential was revoked. "
                f"Server said: {resp.text[:300]}"
            )
        if resp.status_code != 200:
            raise TokenError(
                f"/generate_token failed ({resp.status_code}) at {self.token_url} for "
                f"client {self.client_id!r}: {resp.text[:400]}"
            )
        data: dict[str, Any] = resp.json()
        token = data.get("token") or data.get("access_token")
        if not token:
            raise TokenError(f"token endpoint returned no token; keys={list(data)}")

        self._token = token
        self.scope = data.get("scope")
        self._expiry = self._parse_expiry(data) or (decode_exp(token) or time.time() + 900)
        return token

    @staticmethod
    def _parse_expiry(data: dict[str, Any]) -> float:
        """expires_at is ISO-8601 UTC (e.g. 2026-08-25T10:18:38.75+00:00)."""
        raw = data.get("expires_at")
        if not raw:
            ttl = data.get("expires_in")
            return time.time() + float(ttl) if ttl else 0.0
        try:
            from datetime import datetime

            return datetime.fromisoformat(str(raw).replace("Z", "+00:00")).timestamp()
        except (ValueError, TypeError):
            return 0.0
