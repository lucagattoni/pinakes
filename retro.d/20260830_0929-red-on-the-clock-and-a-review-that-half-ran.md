## Red on the clock, and five measurements of one string that all failed (20260830 09:29)

**MEDIUM — a suite went red with no commit, and the design had already decided it should not.**
`prices.toml` aged past `max_price_age_days` (30) on 20260827 and 25 tests began failing. Not one
line of code changed. `docs/DESIGN.md` §5 had **chosen** a runtime refusal plus a `doctor` WARN so
staleness would not gate a build — and then 25 tests asserted the un-stale path **without pinning a
clock**, so the suite quietly became the gate the design refused. **The defect is neither the
constant nor the table's age: it is a test that inherits today's date and asserts an outcome that
depends on it.**

**And the precedent cited against wall-clock checks was this file.** `tools/status_header_gate.py:52`
declines a staleness check because *"a wall-clock staleness check fails on a quiet weekend with no
code change"* — **naming `prices.toml` as the reason not to add one.** `prices.toml` then did
exactly that, after a quiet four days.

**MEDIUM — two adversarial reviews died the same way within hours, and both reported a clean bill.**
52 agents, 26 dead; 19 agents, 17 dead, the second returning a literal
`{"raised":0,"confirmed":[],"refuted":[]}`. **Two independent instances in one day is the contract,
not bad luck** — a dead agent becomes `null` and `.filter(Boolean)` erases the evidence. Both were
recoverable from agent transcripts on disk, which makes it a **procedure** rather than a warning.
`tools/review_ledger.py` exits 1 on an unfinished pass and would have caught both **before either
result was read**. A third hole was nobody's session limit: the workflow capped a lens at
`.slice(0, 12)` when it raised **16**, and logged nothing. Three of the four dropped were real.

**HIGH, and it is about the author rather than the tools: five measurements of one string failed
before the truth came out.** The claim was that a fragment *"written in `d9fe1a9`"* carried the
phrase *"wrong for twelve hours"*. Checking it:

| attempt | result | why it lied |
|---|---|---|
| `grep` for the phrase | no match | the phrase was **wrapped across a newline**; `grep` is line-based |
| `tr '\n' ' '` then match | no match | Markdown **indentation** left multiple spaces between the words |
| the same check in a shell `for` loop | `0` for every sha | a **quoting artifact**; the file plainly contained it |
| reading `29856b9` | "confirmed true" | **the sentence names `d9fe1a9`**, a different commit |
| `uv run … \| grep …; echo $?` on a gate | `0` on a failing run | `$?` is **`grep`'s** status |

**The claim was false and three independent agents said so while the author confirmed it twice.**
Four of those five failures are the same shape: *a check that answers a narrower question than the
one asked, and returns something indistinguishable from a clean result.* **A shell one-liner
composed in the moment is not an instrument** — and the author is the least reliable verifier of the
author's own text, which is the case for spending agents on prose nobody else has read.

**LOW — and the handover rule caught itself.** All of the above lived only in `RESUME.md`, which
[`docs/BUILDING.md`](https://github.com/lucagattoni/pinakes/blob/main/docs/BUILDING.md) calls **"a
convenience, never a carrier"**: excluded from git, invisible to every other checkout, *"cannot
discover that one exists"*. **The rule is the planner's own and the planner broke it** — by putting
a repository-wide blocker somewhere no other session could ever find. That is what this commit fixes.
