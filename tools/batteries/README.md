# Mutation batteries

One TOML file per target, run by [`tools/mutate.py`](../mutate.py), which is the mutation step of
[`docs/BUILDING.md`](../../docs/BUILDING.md) § *One increment at a time* → 4.

    python3 tools/mutate.py tools/batteries/tools-release_order_gate.toml
    python3 tools/mutate.py --check-anchors tools/batteries/*.toml

Each row says: **break the code this way, and this named test dies.** A row is a claim about *one
assertion*, never about a commit and never about the file — a battery of forty-one kills does not
say the gate is correct, it says these forty-one breakages are each noticed by a test that names
them.

## Why these are committed

Batteries used to be per-increment working files, discarded with the session that wrote them.
`tools/mutate.py`'s docstring said so as a matter of design. It was an assumption, and on
**20260823** it was measured against 81 mutants written across six increments and left in session
scratchpads:

| | |
|---|---|
| Anchors that still resolved exactly once, a day to a week later | **78 of 81** |
| The three that did not | **refused** — named, counted, exit 1, target untouched |
| Anchors that broke when their own code did not change | **0** |
| The one *comment-bearing* anchor in the set | the one that went ambiguous |

So the failure mode of keeping a battery is a **maintenance prompt, never a false certificate**. A
stale anchor cannot produce a false `KILLED` or a false `SURVIVED`: `mutate.py` resolves every
anchor in the batch before it writes anything, and refuses on 0 matches and on 2.

What being kept preserves is **not the proof**. Re-deriving forty-one mutants against a gate is an
afternoon's work. It is the *reasoning about which mutants were worth writing* — which breakages are
plausible, which one is the shipped defect the increment closed, and which two exist only because a
first-draft guard-test turned out to be a tautology. None of that is in the code, and none of it is
re-derivable from the code.

## How a battery earns its name

**A battery is named for its primary target: the path, `/` → `-`, extension dropped.**

    tools/release_order_gate.py  →  tools/batteries/tools-release_order_gate.toml
    src/pinakes/graph/traverse.py → tools/batteries/src-pinakes-graph-traverse.toml

Mechanical, and collision-free for any two distinct paths. If two targets ever do collide — a
`check.sh` and a `check.py` — the second keeps its extension.

**A battery may mutate more than one file when the guarantee spans more than one.**
`tools-mcp_handshake_gate.toml` mutates a gate, a server, two workflows, a Makefile recipe and a
dependency floor, because the thing it protects — *a published wheel still answers `initialize` with
Pinakes' own name, version and tool list* — lives in all six. Three of its mutants are the same idea
in three files (`| tee`, `|| true`, `set +e`: a gate is only a gate when its exit status is what the
next command reads). Split by file, that pattern is invisible.

**Adding a mutant: grep first.**

    grep -l 'file = "src/pinakes/serve.py"' tools/batteries/*.toml

One hit → add it there. No hits → start a battery named for that file. **Two hits is a defect**, and
`--check-anchors` fails on it: a file belongs to exactly one battery, so an increment touching it
again has one place to add to and cannot leave two sets of mutants that can disagree. That is the
whole reason these are one-file-per-target rather than one-file-per-increment.

**An increment appends a section; it never starts a second file for a target that already has one.**
Sections are ordered oldest release first and say which release shipped the property.

## What `--check-anchors` sees, and what it cannot

It resolves every anchor against the **working tree** — not `HEAD`, because nothing is written and
requiring a clean tree would disarm the check in the one moment it is wanted, mid-refactor. It
reports *every* failure rather than the first, since a repair wants the whole list. It runs no
subprocess and takes milliseconds.

It **cannot** see two things, and says so on success rather than leaving a green line to be misread:

- **a `kills` selector naming a test that has been renamed away.** Caught by `mutate.py`'s baseline
  run, which needs pytest — a selector that collects nothing is refused there, never treated as a
  survival.
- **an anchor that still matches while the code around it moved**, so the mutant would be `KILLED`
  about a property nobody tests any more. **Nothing detects this.** It is why a mutant's `name`
  states what the breakage *is* rather than what the edit does: the name is what a reader compares
  against the code, and it is the only guard there is.

A green `--check-anchors` is therefore not a green run. Run the battery.

## When an anchor rots

It rots loudly — `mutate.py` names the anchor and its count and exits 1 with the file untouched. Two
repairs, both from the measurement above, are the whole vocabulary:

- **0 matches** — the code moved. Find the property, re-anchor on it, and say in a comment what
  changed. (`ascending=True` / `minimum=15,` stopped being adjacent when `starts_at` landed between
  them.)
- **2 matches** — a second call site appeared. Widen the anchor by one *stable* neighbouring line,
  not by a comment. (A second `newest_may_lag=True,` arrived with the seventh sequence; the
  `minimum=15,` above it belongs to that sequence alone.)

If the property itself is gone, delete the mutant and say so in the section. A battery that no
longer describes the code is worse than no battery.

## Conventions

- **No `pytest` key.** A committed battery takes the default, `uv run --frozen pytest` — one less
  thing in the file that can rot. Keep it only for a battery that genuinely needs another runner.
- **Targets under `tests/` are refused** by `mutate.py` and stay manual: a mutant in the file its
  own selector runs can make that test vacuous, and no printed outcome would say so.
- **Comments carry the reasoning.** They are the reason these files exist; `mutate.py` ignores
  them and a reader does not.
