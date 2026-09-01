## A composed number, again — and a test that was not a pin (20260901 06:31)

Two findings from the adversarial pass over the `--questions` guard, kept because neither is about
`--questions`.

**HIGH — the third block of the guard's own test asserted nothing.** It claimed to catch the
plausible widening of the guard to the KB's *default* golden set, and its KB was
`tmp_path / "kb-without-a-golden-set"` with `mkdir()`. An empty directory has no `pinakes.toml`, so
`load()` raised `ManifestError` and execution never reached the default questions path at all. Both
assertions — `returncode != 2`, `"no golden set at" not in stderr` — were satisfied by that
unrelated crash. The reviewer patched the widened guard in and the test **passed**. It is a real
copy of the demo KB now, with only `eval/questions.yaml` removed, plus a third assertion that the
default path was actually reached, and mutant 6 in the battery is the widening it now kills.

The rule this breaks is the house one: *a test is a pin only if reverting the fix turns it red*. The
subtler half is that I never applied it here, because there was no fix to revert — the block asserts
a **non-**behaviour, that something is deliberately *not* guarded. A negative assertion has no fix to
back out, so the pin test has to be run forward instead: **apply the change the block exists to
forbid, and watch it go red.** Nothing in the procedure said to do that, and I did not.

**MEDIUM — "a nine-frame `FileNotFoundError`". It is five.** Module, `main`, `load_questions`,
`read_text`, `open`, measured on `b47eda6`. The number went into the commit message, into a comment
in shipped code, and into the test's docstring, in the same phrasing three times. Nobody counted it.

**That is the second composed number on this branch in one evening, and the fourth of the day
across sessions.** The first was a quotation attributed to a plan row that the row does not contain;
this one is an integer attributed to a traceback nobody ran. The pattern is not carelessness about
facts in general — every *load-bearing* claim on this branch was measured. It is that a number used
as **texture**, to make a sentence concrete, does not feel like a claim while it is being written.
`retro.d/README.md` already names this exact failure for timestamps — *"composing it instead is the
failure this rule exists to stop"* — and the timestamp rule works because it names the instrument:
`date -u`, once, pasted twice. A frame count has no such instrument, so: **if a sentence contains a
number, either it came from a command in this session's scrollback or it does not go in.**

Both were found by review lenses, not by me, and neither would have been found by re-reading: one
needed a patched mutant, the other needed `grep -c '  File '` on a traceback nobody had generated.
That is the same conclusion the day's other four wrong claims reached from four different
directions — **re-running is what catches these; re-reading is not.**
