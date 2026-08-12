## E5 — The run transcript (20260812 05:11)

**MEDIUM — a mutation restored a file and silently took a real edit with it.** The mutation pass
works by editing a source file, running the suite, then `git checkout <file>`. Between the first
commit and mutation 5 there was exactly one source edit — a comment in `cli.py` correcting a claim
about `clear_cache_paid` — and `git checkout src/pinakes/cli.py` reverted it along with the
mutation. Nothing failed: the tests pass either way, `./check.sh` is green, and the reverted text
was a *comment*, so no gate could see it. It was found by reading the increment's own diff in the
adversarial pass and noticing the comment said what the earlier draft said.

The lesson is narrow and mechanical: **`git checkout` restores to the last commit, not to the state
before the mutation.** Either commit before mutating, or restore with `git stash`/a copy. This
increment did the former for the code and got caught by the one edit that landed in between.

**MEDIUM — a test that asserted the wrong half of its own claim.** "The temp file is `.tmp`, not
`.json`, so a killed write leaves nothing the readers count" was tested by *planting* a
`.tmp-abcdef.tmp` file and checking the glob ignored it. That proves the glob ignores `.tmp` files.
It says nothing about what the writer names its temporaries, and it kept passing when the suffix was
mutated to `.json`. It now spies on `os.replace`, whose source argument **is** the file a kill one
instruction earlier would have left behind, and asserts on that name.

Generalisable: **when a test plants the input it then checks, ask which half of the claim it
actually reaches.** The planted value came from the test's understanding of the code rather than
from the code, so the two could disagree without the test noticing — which is the whole failure mode
the mutation pass exists to find, and it found it.

**LOW — the confirm-then-re-call path had never been tested, on either store.**
`sys.stdin.isatty()` is `False` under pytest, so every `--clear-cache` test since I4 took the
`--yes` route straight past the prompt, the `y`/`n` branch and the second `sync()` call. Three tests
now walk it. Worth recording because the gap was invisible in the ordinary way: the flag had
coverage, the *interactive* flag did not, and no coverage number distinguishes them.

**A decision worth writing down: `--clear-cache=transcripts` names a store, and the two values
before it name authorisations.** `--clear-cache` and `--clear-cache=paid` both clear the whole
extraction cache and differ only in what they permit — a documented distinction, with a comment in
`cli.py` explaining why the bare form is not called `=free`. Layering `transcripts` onto that axis
would have meant `--clear-cache=transcripts` also emptying the extraction cache, which destroys more
than the flag names. Mixing the two axes in one flag is a real cost, and it was paid deliberately
rather than by accident: D-26 asked for a `--clear-cache` target, and a target is what it is.

**What E6 inherits.** The transcript is the record the measurement run reports out of: it carries
`call_ids`, the estimate and the reconciled spend per run, so the over-reservation factor E6 must
publish can be computed from the files a measured run leaves behind rather than from a spreadsheet
kept beside it. `transcript.call_ids()` plus `sync.ledger_spend()` is the join, already written for
the confirmation prompt.
