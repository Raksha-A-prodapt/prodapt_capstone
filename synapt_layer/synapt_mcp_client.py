"""Ask questions through a local Synapt MCP bridge."""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

DEFAULT_URL = os.getenv(
    "SYNAPT_MCP_URL",
    "http://127.0.0.1:8000/mcp",
)


async def ask_synapt(
    question: str,
    url: str = DEFAULT_URL,
) -> dict[str, object]:
    """Return a concise answer and useful metadata from Synapt."""
    if not question.strip():
        raise ValueError("Synapt question cannot be empty.")

    try:
        async with streamable_http_client(url) as (
            read_stream,
            write_stream,
            _,
        ):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.call_tool(
                    "ask_synapt",
                    {"question": question},
                )
    except Exception as exc:
        raise RuntimeError(
            f"Could not connect to the Synapt MCP server at {url}. "
            "Check that the server is running and that SYNAPT_MCP_URL "
            "points to its Streamable HTTP endpoint."
        ) from exc

    if result.isError:
        error_text = "\n".join(
            text
            for item in result.content
            if (text := getattr(item, "text", None))
        )
        raise RuntimeError(
            "Synapt's ask_synapt tool returned an error"
            + (f": {error_text}" if error_text else ".")
        )

    response_text = "\n".join(
        text
        for item in result.content
        if (text := getattr(item, "text", None))
    ).strip()
    if not response_text:
        raise RuntimeError(
            "Synapt's ask_synapt tool returned no text content."
        )

    try:
        parsed_response = json.loads(response_text)
    except json.JSONDecodeError:
        return {"answer": response_text}

    if not isinstance(parsed_response, dict):
        return {"answer": response_text}

    answer = parsed_response.get("answer")
    if not isinstance(answer, str) or not answer.strip():
        return {"answer": response_text}

    useful_fields = (
        "query_id",
        "task_id",
        "confidence_score",
        "ks_confidence",
        "ps_confidence",
        "graph_confidence",
        "trust_signal",
        "warnings",
        "resolved_mode",
        "intent",
    )
    return {
        "answer": answer.strip(),
        **{
            key: parsed_response[key]
            for key in useful_fields
            if key in parsed_response
        },
    }


async def get_synapt_procedures(
    query: str,
    url: str = DEFAULT_URL,
) -> Any:
    """Retrieve procedures from Synapt for a recommendation request."""
    if not query.strip():
        raise ValueError("Synapt procedure query cannot be empty.")

    try:
        async with streamable_http_client(url) as (
            read_stream,
            write_stream,
            _,
        ):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.call_tool(
                    "get_synapt_procedures",
                    {"query": query},
                )
    except Exception as exc:
        raise RuntimeError(
            f"Could not connect to the Synapt MCP server at {url}. "
            "Check that the server is running and that SYNAPT_MCP_URL "
            "points to its Streamable HTTP endpoint."
        ) from exc

    if result.isError:
        error_text = "\n".join(
            text
            for item in result.content
            if (text := getattr(item, "text", None))
        )
        raise RuntimeError(
            "Synapt's get_synapt_procedures tool returned an error"
            + (f": {error_text}" if error_text else ".")
        )

    response_text = "\n".join(
        text
        for item in result.content
        if (text := getattr(item, "text", None))
    ).strip()
    if not response_text:
        raise RuntimeError(
            "Synapt's get_synapt_procedures tool returned no content."
        )

    try:
        response = json.loads(response_text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "Synapt's get_synapt_procedures tool returned invalid JSON."
        ) from exc
    if not isinstance(response, (dict, list)):
        raise RuntimeError(
            "Synapt's get_synapt_procedures tool returned an unexpected response."
        )
    return response


async def ask(url: str, question: str) -> int:
    """CLI adapter that prints a Synapt response and returns an exit code."""
    try:
        reply = await ask_synapt(question, url)
        print(reply["answer"])
        if "confidence_score" in reply:
            print(f"\nSynapt confidence: {reply['confidence_score']}")
        warnings = reply.get("warnings")
        if warnings:
            print(f"Synapt warnings: {', '.join(map(str, warnings))}")
    except Exception as exc:
        print(f"Request failed: {exc}", file=sys.stderr)
        return 1

    return 0


async def main() -> int:
    parser = argparse.ArgumentParser(
        description="Send a question to the local Synapt MCP bridge."
    )
    parser.add_argument(
        "--url",
        default=DEFAULT_URL,
        help=f"MCP server URL (default: {DEFAULT_URL})",
    )
    parser.add_argument("question", nargs="?", help="ask one question and exit")
    args = parser.parse_args()

    if args.question:
        return await ask(args.url, args.question)

    print(f"Connected questions will use: {args.url}")
    print("Enter a question, or type 'exit' to quit.")
    while True:
        try:
            question = input("\nQuestion> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if question.lower() in {"exit", "quit"}:
            return 0
        if not question:
            continue
        status = await ask(args.url, question)
        if status:
            return status


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

#runs on http://127.0.0.1:8000 server