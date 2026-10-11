# -*- coding: utf-8 -*-
"""Environment-backed configuration for the Trident MCP query agent.

Follows the "Registered Agent Integration Guide": the agent exchanges a
``client_id`` / ``client_secret`` for a short-lived session token at
``<mcp base>/generate_token``, then presents that token as a Bearer credential
on every MCP tool call. Everything here comes from a project ``.env``; nothing
about the deployment or the agent's identity is hard-coded.

Auth mode is resolved by `auth_mode`, in this order:

* ``secret``    - ``SYNAPT_AGENT_CLIENT_SECRET`` (the registry-issued secret) is
  exchanged for a session token. This is the registered-agent flow and the
  normal mode.
* ``static``    - ``SYNAPT_AGENT_TOKEN`` is a session token pasted straight in
  (e.g. from the curl in the guide). Handy for a quick check; it expires.

Agent registration is done for you by the platform team; by the time this runs,
the client_id/secret exist and the grant is approved.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"

# The registered-agent MCP base (section 3 of the guide). Tool calls POST here;
# the token endpoint is this + "/generate_token".
DEFAULT_MCP_URL = "https://beta.synapt.ai/api/mcp"


def load_env() -> None:
    load_dotenv(ENV_PATH, override=False)


class ConfigError(RuntimeError):
    """A required environment variable is missing or malformed."""


def _req(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ConfigError(f"{name} is not set in {ENV_PATH}")
    return value


def _list(name: str, default: str = "") -> list[str]:
    raw = os.getenv(name, default) or ""
    return [p for p in (x.strip() for x in raw.replace(",", " ").split()) if p]


def tls_setting() -> bool | str:
    """SYNAPT_VERIFY_SSL: 'false' to disable, a path to a CA bundle, else True.

    beta.synapt.ai presents a self-signed chain, so verification is usually off
    there; pointing this at the internal CA bundle validates properly instead.
    """
    raw = os.getenv("SYNAPT_VERIFY_SSL", "").strip()
    if not raw:
        return True
    if raw.lower() in {"false", "0", "no", "off"}:
        return False
    if raw.lower() in {"true", "1", "yes", "on"}:
        return True
    return raw


@dataclass
class AgentConfig:
    """Endpoints plus the credential this agent authenticates with."""

    mcp_url: str
    provider_id: str
    client_id: str = ""
    client_secret: str = ""
    static_token: str = ""
    token_url_override: str = ""
    verify: bool | str = True
    timeout: float = 120.0

    @property
    def token_url(self) -> str:
        """<mcp base>/generate_token, unless explicitly overridden."""
        if self.token_url_override:
            return self.token_url_override
        return self.mcp_url.rstrip("/") + "/generate_token"

    @property
    def auth_mode(self) -> str:
        if self.static_token:
            return "static"
        if self.client_secret:
            return "secret"
        return "unset"

    @classmethod
    def from_env(cls, **overrides) -> "AgentConfig":
        load_env()

        # The registered-agent endpoint (/api/mcp) is used verbatim: a trailing
        # slash makes it 307-redirect, so we do NOT normalise it here.
        mcp_url = (os.getenv("SYNAPT_MCP_URL", "").strip() or DEFAULT_MCP_URL).rstrip()

        cfg = cls(
            mcp_url=mcp_url,
            provider_id=_req("SYNAPT_PROVIDER_ID"),
            client_id=os.getenv("SYNAPT_AGENT_CLIENT_ID", "").strip(),
            client_secret=os.getenv("SYNAPT_AGENT_CLIENT_SECRET", "").strip(),
            static_token=os.getenv("SYNAPT_AGENT_TOKEN", "").strip(),
            token_url_override=os.getenv("SYNAPT_AGENT_TOKEN_URL", "").strip(),
            verify=tls_setting(),
            timeout=float(os.getenv("SYNAPT_QUERY_TIMEOUT", "120")),
        )

        if cfg.auth_mode == "secret" and not cfg.client_id:
            raise ConfigError(
                "SYNAPT_AGENT_CLIENT_SECRET is set but SYNAPT_AGENT_CLIENT_ID is not. "
                "The registered-agent flow needs both."
            )
        if cfg.auth_mode == "unset":
            raise ConfigError(
                "no credential: set SYNAPT_AGENT_CLIENT_ID + SYNAPT_AGENT_CLIENT_SECRET "
                "(the registered-agent flow), or paste a session token into "
                "SYNAPT_AGENT_TOKEN."
            )
        if not cfg.client_id:
            cfg.client_id = "(static token)"

        for key, value in overrides.items():
            setattr(cfg, key, value)
        return cfg
