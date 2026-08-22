#!/usr/bin/env python3
"""Drive a real MCP session against `pnk serve` and check what a client actually receives.

**Why a script and not four lines of `printf` in a workflow.** Until 0.27.2 the handshake was
hand-rolled JSON-RPC piped into `pnk serve`: three lines written, then stdin closed. Under `mcp`
1.28.1 the server drained the queue before shutting down, so `tools/list` was answered every time.
Under 2.0.0 it is not — measured 20260822 14:35, the same three lines answered `tools/list`
**2 times out of 10**, with `initialize` answered all 10. A gate that flakes 8 runs in 10 is worse
than no gate: the first red run gets rerun, the second gets believed. Driving the session with
`mcp`'s own client removes the race at its source — the client holds the connection open until it
has its answers — and it negotiates the protocol version itself, so this gate tracks the dependency
instead of rotting against it (a client asking for `2024-11-05`, which is what the workflow used to
send, now gets a session that answers `initialize` and nothing else).

**What it asserts, and why each one is not satisfiable by something else:**

* `serverInfo.name` is `pinakes` — and `serverInfo.version` is the version passed in with
  `--expect-version`, which the caller reads from a source that is *not* `pinakes.__version__`
  (CI reads it out of the built wheel's filename). Every release up to 0.27.2 advertised the *mcp
  library's* version here, because `FastMCP` had no `version=` parameter and filled the field
  itself; a client asking which Pinakes it was talking to was told `1.28.1`.
* the tools the server lists are **exactly** the snapshot in `--snapshot`, compared as JSON with
  keys sorted — names, descriptions, `inputSchema` and `outputSchema`. Both `FastMCP` and
  `MCPServer` derive those schemas from Python signatures and docstrings, and nothing promises two
  libraries derive the same one. They were byte-identical at the port (20260822), which is a
  measurement, not a guarantee: run against a *freshly resolved* dependency set, this is what turns
  a future mcp release quietly reshaping the published tool contract into a red run.

The snapshot is regenerated only by `--update-snapshot`, never as a side effect of a check, because
a gate that repairs its own expectation asserts nothing.
"""

from __future__ import annotations

import argparse
import asyncio
import difflib
import json
import shutil
import sys
from pathlib import Path
from typing import Any

DEFAULT_SNAPSHOT = Path(__file__).with_name("mcp_tool_schemas.json")
# A whole session — spawn, initialize, list — against an empty KB takes well under a second. Ten is
# far enough above that to never fire on a slow runner, and near enough that a hang costs seconds
# rather than the job's `timeout-minutes`.
SESSION_TIMEOUT_SECONDS = 30.0


class GateError(Exception):
    """A failure to report on stderr and exit non-zero for. Never raised for a check that passed."""


async def _session_payload(command: str, kb: Path) -> dict[str, Any]:
    """Spawn `<command> serve <kb>`, complete a real MCP session, and return what it answered."""
    # Imported here, not at module scope: the error a missing `mcp` deserves is this gate's own
    # message naming the environment it was run in, not a traceback out of argparse.
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    parameters = StdioServerParameters(command=command, args=["serve", str(kb)])
    async with stdio_client(parameters) as (read, write), ClientSession(read, write) as session:
        initialized = await session.initialize()
        listed = await session.list_tools()
    return {
        "server_info": initialized.server_info.model_dump(mode="json", by_alias=True),
        "protocol_version": initialized.protocol_version,
        "tools": listed.model_dump(mode="json", by_alias=True, exclude_none=True)["tools"],
    }


def _normalise(tools: list[dict[str, Any]]) -> str:
    """The comparable form of a tool list: ordered by name, keys sorted, one trailing newline.

    Ordering is imposed rather than assumed. Registration order is what both libraries happen to
    return today, and a snapshot that depends on it would fail the day one of them iterates a dict
    differently — a failure about nothing, in the gate whose whole value is that a failure means
    something.
    """
    ordered = sorted(tools, key=lambda tool: str(tool["name"]))
    return json.dumps(ordered, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _check_server_info(server_info: dict[str, Any], expected_version: str) -> None:
    name = server_info.get("name")
    if name != "pinakes":
        raise GateError(f"serverInfo.name is {name!r}, expected 'pinakes'")
    version = server_info.get("version")
    if version != expected_version:
        raise GateError(
            f"serverInfo.version is {version!r}, expected {expected_version!r}. Until 0.27.2 this "
            f"field carried the mcp library's own version, which is what the `version=` argument "
            f"to MCPServer exists to stop"
        )


MISSING_SNAPSHOT = "nothing to compare against"
"""Checked before the server is ever spawned, so a run with no snapshot cannot report a passing
session and then discover it had no expectation to hold it to."""


def _check_tools(tools: list[dict[str, Any]], snapshot: Path) -> None:
    actual = _normalise(tools)
    expected = snapshot.read_text(encoding="utf-8")
    if actual == expected:
        return
    diff = "".join(
        difflib.unified_diff(
            expected.splitlines(keepends=True),
            actual.splitlines(keepends=True),
            fromfile=f"{snapshot} (committed)",
            tofile="what the server just listed",
        )
    )
    raise GateError(
        f"the tools this server lists are not the ones {snapshot} records. That is a change to the "
        f"published MCP contract, not a detail — every client reads these schemas:\n{diff}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--kb", type=Path, required=True, help="a KB directory to serve")
    parser.add_argument(
        "--expect-version",
        help="the version serverInfo must advertise. Read it from a source other than "
        "pinakes.__version__ — the built wheel's filename, say — or the check compares a "
        "constant with itself",
    )
    parser.add_argument(
        "--snapshot",
        type=Path,
        default=DEFAULT_SNAPSHOT,
        help=f"the committed tool schemas to compare against (default: {DEFAULT_SNAPSHOT})",
    )
    parser.add_argument(
        "--command", default="pnk", help="the Pinakes entry point to spawn (default: pnk)"
    )
    parser.add_argument(
        "--update-snapshot",
        action="store_true",
        help="rewrite --snapshot from what the server lists, and check nothing else",
    )
    args = parser.parse_args(argv)

    if not args.update_snapshot and not args.expect_version:
        parser.error("--expect-version is required unless --update-snapshot is given")
    if not args.kb.is_dir():
        print(f"mcp-handshake-gate: no KB directory at {args.kb}", file=sys.stderr)
        return 1
    if shutil.which(args.command) is None:
        print(
            f"mcp-handshake-gate: {args.command!r} is not on PATH — the gate never reached a "
            f"server, so nothing here was checked",
            file=sys.stderr,
        )
        return 1
    if not args.update_snapshot and not args.snapshot.is_file():
        print(
            f"mcp-handshake-gate: no snapshot at {args.snapshot} — {MISSING_SNAPSHOT}. Create it "
            f"deliberately with --update-snapshot; a check will not write one for you",
            file=sys.stderr,
        )
        return 1

    try:
        payload = asyncio.run(
            asyncio.wait_for(
                _session_payload(args.command, args.kb), timeout=SESSION_TIMEOUT_SECONDS
            )
        )
    except TimeoutError:
        print(
            f"mcp-handshake-gate: no complete session in {SESSION_TIMEOUT_SECONDS:.0f}s — "
            f"`{args.command} serve` did not answer",
            file=sys.stderr,
        )
        return 1
    except Exception as error:  # noqa: BLE001 — the gate reports, it does not raise at a workflow
        print(f"mcp-handshake-gate: the session failed: {error!r}", file=sys.stderr)
        return 1

    tools: list[dict[str, Any]] = payload["tools"]
    if args.update_snapshot:
        args.snapshot.write_text(_normalise(tools), encoding="utf-8")
        print(f"mcp-handshake-gate: wrote {len(tools)} tools to {args.snapshot}")
        return 0

    try:
        _check_server_info(payload["server_info"], str(args.expect_version))
        _check_tools(tools, args.snapshot)
    except GateError as failure:
        print(f"mcp-handshake-gate: {failure}", file=sys.stderr)
        return 1

    names = ", ".join(sorted(str(tool["name"]) for tool in tools))
    print(
        f"mcp-handshake-gate: pinakes {args.expect_version} answered over MCP "
        f"{payload['protocol_version']} and listed {len(tools)} tools matching "
        f"{args.snapshot.name}: {names}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
