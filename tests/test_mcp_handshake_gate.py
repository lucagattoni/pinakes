"""`tools/mcp_handshake_gate.py`, driven as a subprocess — one test per branch.

A subprocess rather than an import, for the reason `tests/test_wheel_import_gate.py` gives: it
exercises the same artifact the workflows run, argument parsing included, with no `sys.path`
surgery.

**Unlike the wheel-import gate's tests, one of these is not about the gate.**
`test_a_real_session_lists_exactly_the_committed_tool_schemas` spawns `pnk serve` and compares what
a real MCP client is handed against `tools/mcp_tool_schemas.json`, so it is the local guard on the
published tool contract: rename a `pinakes_*` function, reword a tool docstring, or change a
parameter's type, and it goes red naming the change. It runs against the *locked* `mcp`, so it
cannot see a future release of that library reshaping the schemas — the same run in CI's `build`
job, against a fresh resolve, is what sees that, and this test is what keeps the gate it uses
honest in between.
"""

import importlib.metadata
import json
import subprocess
import sys
from pathlib import Path

import pytest

from pinakes.init import init

TOOL = Path(__file__).parent.parent / "tools" / "mcp_handshake_gate.py"
SNAPSHOT = Path(__file__).parent.parent / "tools" / "mcp_tool_schemas.json"

INSTALLED = importlib.metadata.version("pinakes")
"""Read from the installed distribution's metadata rather than imported from `pinakes.__version__`.

Both ultimately come from `pyproject.toml`, but by different routes and at different times — the
metadata is written when the package is installed, the constant when the module is imported — and
the point of the assertion is that the *server* advertises the version this environment believes
it has. Comparing `__version__` with `__version__` would hold with the `version=` argument deleted.
"""

MCP_VERSION = importlib.metadata.version("mcp")
"""The version every Pinakes release up to 0.27.2 advertised as its own."""


def run(*args: str, timeout: float = 90.0) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(TOOL), *args],
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
    )


@pytest.fixture(scope="module")
def kb(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """An empty initialised KB — enough to serve, and nothing to index.

    Module-scoped because every test here that reaches a session pays for one `pnk serve` spawn
    already; paying for a `pnk init` per test as well buys nothing, since no test writes to it.
    """
    root = tmp_path_factory.mktemp("handshake") / "kb"
    init(root, name="handshake", now="20260822 14:00")
    return root


def test_a_real_session_lists_exactly_the_committed_tool_schemas(kb: Path) -> None:
    """The contract check, and the only test here that would notice a change to `serve.py`.

    A real `ClientSession` over stdio, not hand-rolled JSON-RPC. That distinction is the reason
    the gate exists: three lines written to `pnk serve` followed by a closed stdin answered
    `tools/list` **2 times in 10** under mcp 2.0.0 and 10 in 10 under 1.28.1 (measured
    20260822 14:35). A test flaking 8 runs in 10 is worse than no test.
    """
    result = run("--kb", str(kb), "--expect-version", INSTALLED)
    assert result.returncode == 0, result.stdout + result.stderr
    for tool in ("pinakes_search", "pinakes_get", "pinakes_links", "pinakes_list_kbs"):
        assert tool in result.stdout, f"the gate passed without naming {tool}: {result.stdout}"


def test_the_version_a_client_is_told_is_pinakes_own_and_not_the_mcp_librarys(kb: Path) -> None:
    """The defect this increment fixed, asserted from the failing side.

    `FastMCP` took no `version=`, so it filled `serverInfo.version` with the version of `mcp`
    itself — every published release told a client asking which Pinakes it was talking to that it
    was `1.28.1`. Handing the gate that same value must fail, and asserting it fails *for the
    version* rather than for any reason at all is what makes this more than a non-zero exit.
    """
    assert INSTALLED != MCP_VERSION, "this test cannot distinguish them if they are equal"
    result = run("--kb", str(kb), "--expect-version", MCP_VERSION)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "serverInfo.version" in result.stderr, result.stderr
    assert MCP_VERSION in result.stderr and INSTALLED in result.stderr, (
        "the failure must name both what was advertised and what was expected, or a reader "
        "cannot tell which of the two is wrong"
    )


def test_a_snapshot_that_does_not_match_fails_and_shows_which_line_moved(
    kb: Path, tmp_path: Path
) -> None:
    """A mismatch is a change to the published contract, so the failure has to be readable as one.

    The mutation is a renamed tool because that is the cheapest change with the widest blast
    radius: every client that calls `pinakes_get` by name breaks, and nothing else about the
    server looks different.
    """
    tools = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    renamed = next(tool for tool in tools if tool["name"] == "pinakes_get")
    renamed["name"] = "pinakes_fetch"
    altered = tmp_path / "altered.json"
    altered.write_text(
        json.dumps(sorted(tools, key=lambda t: str(t["name"])), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    result = run("--kb", str(kb), "--expect-version", INSTALLED, "--snapshot", str(altered))
    assert result.returncode == 1, result.stdout + result.stderr
    assert '-    "name": "pinakes_fetch"' in result.stderr, result.stderr
    assert '+    "name": "pinakes_get"' in result.stderr, result.stderr


def test_a_missing_snapshot_is_refused_before_a_server_is_ever_spawned(
    kb: Path, tmp_path: Path
) -> None:
    """A gate with no expectation must not report a passing session.

    Refused *before* the spawn, not after: a run that starts a server, completes a session and
    then discovers it had nothing to compare against has already printed the reassuring half of
    its output. The absent file must also stay absent — a check that writes the snapshot it is
    missing asserts nothing ever again.
    """
    absent = tmp_path / "nothing-here.json"
    result = run("--kb", str(kb), "--expect-version", INSTALLED, "--snapshot", str(absent))
    assert result.returncode == 1, result.stdout + result.stderr
    assert "nothing to compare against" in result.stderr, result.stderr
    assert not absent.exists(), "a check wrote the snapshot it was supposed to compare against"
    assert "answered over MCP" not in result.stdout, (
        "the session ran before the missing snapshot was noticed"
    )


def test_a_command_that_is_not_on_path_is_refused_rather_than_reported_as_a_pass(
    kb: Path,
) -> None:
    """An environment where nothing installed must not look like a passing gate.

    This repository's recorded defect class is an assertion satisfied by something other than the
    property it names, and the sharpest instance is a check that never ran. The message says the
    gate reached no server, which is what a reader of a red log needs first.
    """
    result = run("--kb", str(kb), "--expect-version", INSTALLED, "--command", "pnk-not-installed")
    assert result.returncode == 1, result.stdout + result.stderr
    assert "never reached a server" in result.stderr, result.stderr


def test_a_kb_that_does_not_exist_is_refused(tmp_path: Path) -> None:
    """`pnk serve` on a missing directory fails inside the session with a much worse message."""
    result = run("--kb", str(tmp_path / "absent"), "--expect-version", INSTALLED)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "no KB directory" in result.stderr, result.stderr


def test_expect_version_is_required_unless_the_snapshot_is_being_updated(kb: Path) -> None:
    """Omitted, it would default to something — and every default here is a check that passes.

    `argparse` exits 2 for a usage error, which is neither of the gate's own exit statuses; the
    assertion names 2 rather than "non-zero" so that a future refactor turning this into a silent
    `return 1` shows up as a change in kind.
    """
    result = run("--kb", str(kb))
    assert result.returncode == 2, result.stdout + result.stderr
    assert "--expect-version is required" in result.stderr, result.stderr


def test_update_snapshot_writes_what_the_server_lists_and_checks_nothing(
    kb: Path, tmp_path: Path
) -> None:
    """The one flag that makes the gate a writer, pinned so its blast radius stays visible.

    It ignores `--expect-version` — deliberately, since regenerating the schemas has nothing to do
    with which version advertises them — and that is exactly why it must never appear in a
    workflow. The file it writes has to be the same normalised form a check reads, or the next run
    fails on formatting and the diff is noise.
    """
    fresh = tmp_path / "written.json"
    result = run("--kb", str(kb), "--snapshot", str(fresh), "--update-snapshot")
    assert result.returncode == 0, result.stdout + result.stderr
    assert fresh.read_text(encoding="utf-8") == SNAPSHOT.read_text(encoding="utf-8"), (
        "a regenerated snapshot differs from the committed one — either the contract moved or the "
        "two are not written in the same normalised form"
    )
