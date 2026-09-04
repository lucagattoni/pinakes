# How to read past sessions — the method behind this harvest

**Contributed by the coder session, 20260904 12:15 UTC, and committed here because it arrived as a message
and a message is where a method dies.** Every step was tested against this project's own
transcripts. The planner added nothing except this paragraph and the closing note.

## Where transcripts live

    ~/.claude/projects/<cwd with slashes turned to hyphens>/<session-uuid>.jsonl

For this repository: `~/.claude/projects/-Users-luca-Code-repos-github-lucagattoni-Pinakes/` —
**119 transcripts, 705 MB, oldest session start 2026-07-28, nothing pruned in five weeks.**

**`/clear` does not delete.** It starts a **new** transcript and leaves the old one intact. That is
the whole reason this is possible: every cleared session is still on disk in full. The sibling
directory `<uuid>/` beside each `.jsonl` holds that session's background-task outputs.

## Record structure — one JSON object per line

| field | meaning |
|---|---|
| `type` | `"user"`, `"assistant"`, and others |
| `message` | `{role, content:[...]}`; blocks are `{type:"text",text}`, `{type:"tool_use",id,name,input}` (`input.command` for Bash), `{type:"tool_result",tool_use_id,content,is_error}` |
| `timestamp` | ISO8601 Z |
| `sessionId` | the transcript's **own** uuid — equals the filename |
| `uuid` / `parentUuid` | the message chain |

## The technique that makes outcomes measurable

**Pair `tool_use.id` to the later `tool_result.tool_use_id`.** Without it you count *invocations*;
with it you count **results**.

**This is the step whose absence produced a wrong finding today.** The coder first reported
`check.sh`'s red rate as unrecoverable. With the pairing it is recoverable: **31 red of 139
resolved.** Grepping the command string gives mentions, not runs, and no outcomes at all.

## Six gotchas, each of which bit someone during this harvest

1. **Never `cat` or `Read` a whole transcript** — some exceed 50 MB. Stream line by line.
2. **`tool_result.content` is sometimes a string, sometimes a list of `{type:"text"}` blocks.**
   Handle both or you silently drop half your results.
3. **Backgrounded commands put their output in the task file, not the `tool_result`** — so a gate
   run in the background has an empty-looking result. Follow the later call that reads the log.
   **This gotcha produced the wrong "unrecoverable" conclusion above.**
4. **Auto-generated `/compact` summaries appear as user-role records. They are not the human.**
   Across 14 coder sessions there are only ~42 real human turns; **23 of 49 apparent "correction"
   hits were compaction summaries and 21 more were peer messages.** Filter them or you attribute the
   harness to the user.
5. **A transcript quotes other sessions' ids.** Its own identity is the **filename uuid**. The
   `session_01…` token in commit trailers is a different namespace and **names a lineage, not a
   session** — `/clear` preserves it across transcripts.
6. **Grepping command text under-counts anything inside an `&&` chain**, and this harvest's
   `tool_calls.tsv` keeps only the first two words of a Bash command. **Parse `input.command` from
   the `tool_use` block instead.**
7. **A heredoc writing prose that contains code spans is a command-substitution surface.**
   `cat >> file <<EOF` executes every backtick as a command, so `` `land.py` `` becomes empty and
   takes its own backticks with it. The shell prints one *command not found* line to stderr and
   **exits 0**, so nothing fails; `./check.sh` and `make docs` both pass, because no gate here
   compares written text to what was meant. **Backtick parity does not detect it** — losses come in
   pairs, so the count stays even; a parity check reads as verification and behaves as a placebo.
   Neither does the double-space signature the deletion leaves, because **ignoring code spans in
   order to look for it performs the same deletion** (measured by the coder: 19.0% false positives
   over 40,979 prose lines in 78 files). **Use `<<'EOF'` always** and substitute timestamps
   afterwards, or write the file from Python — and **where a source still exists, diff the landed
   file against it.** That comparison is the only thing that has ever caught this: two artifacts of
   one act, per `FRAMEWORK.md` § 9.5. *Found 20260904 by the planner losing a code span in § 9
   itself; detection ruled out by the coder the same day, reported as a negative result rather than
   shipped as a 19%-false-positive gate.* **The same surface has a loud symptom too**: the coder
   wrote `tools/register_gate.py` through a heredoc and `ruff format` rejected it outright. Nothing
   about that file was wrong — a heredoc simply writes text other tools have opinions about, and the
   gate found it in seconds. **Loud and silent are the same surface with opposite symptoms, and only
   the silent one needs a rule**, which is why this entry is about content loss rather than
   formatting.

## A tested reader

```python
#!/usr/bin/env python3
"""usage: readsession.py <file.jsonl> [--tools]"""

import json, sys

show_tools = "--tools" in sys.argv
for line in open(sys.argv[1]):
    try:
        d = json.loads(line)
    except Exception:
        continue
    msg = d.get("message") or {}
    role, ts = msg.get("role") or d.get("type"), (d.get("timestamp") or "")[:19]
    cont = msg.get("content")
    if isinstance(cont, str):
        cont = [{"type": "text", "text": cont}]
    if not isinstance(cont, list):
        continue
    for b in cont:
        if not isinstance(b, dict):
            continue
        if b.get("type") == "text" and b.get("text", "").strip():
            print(f"\n[{ts}] {role.upper()}:\n{b['text'].strip()}")
        elif show_tools and b.get("type") == "tool_use":
            arg = (
                (b.get("input") or {}).get("command")
                or (b.get("input") or {}).get("file_path")
                or ""
            )
            print(f"\n[{ts}]   -> {b.get('name')}: {str(arg)[:200]}")
```

## Reading a session back into context rather than analysing it as data

    claude --resume          # picker over past sessions
    claude -r <session-id>   # reopen a specific one
    claude -c                # continue the most recent
    --fork-session           # branch instead of continuing in place
    /resume                  # from inside a running session

## Which session is which

`sessions.tsv` maps transcript → `agent_name`, `role`, `start`, `end`. **Filter there first
rather than opening files blind.**

---

**Why this is not a committed tool.** `tools/` is the coder's to write, development is paused, and
nobody asked for one. The reader is inlined so it survives without becoming a maintained surface. If
it should become `tools/readsession.py`, that is for whoever resumes.
