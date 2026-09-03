## S4's fix reproduced S4, on the one value class the framing excluded (20260902 21:18)

S4 was: a KB name containing a quote, a backslash or a control character wrote a `pinakes.toml`
no parser could read, while `pnk init` exited 0 and printed *created*. `pnk init` refuses a
directory that is already a KB, so the remedy surface was empty and recovery meant hand-editing
TOML. The fix escapes every interpolated value for the TOML basic string it lands in.

Measured on the branch that carries that fix, through the real CLI:

    pnk init /tmp/kb --name $'kb-\xff-name'
      → uncaught UnicodeEncodeError from Path.write_text (init.py:370)
      → /tmp/kb/pinakes.toml exists, 0 bytes
      → retry: "error: /tmp/kb is already a KB."

An unreadable manifest, `init` refusing the directory, an empty remedy surface. **The same three
sentences, on the branch whose whole purpose was to delete them.**

### The framing excluded the class, so no amount of care inside it would have found it

`\xff` on a command line is not valid UTF-8, and POSIX decodes it with `surrogateescape` (PEP 383)
into U+DCFF — an unpaired surrogate. TOML's basic string admits `%x80-D7FF` and `%xE000-10FFFF`
raw and skips the gap, and `\uXXXX` must name a Unicode scalar value. **So the character has no
TOML form raw and none escaped.** It is not a hard value to escape; it is a value for which
escaping is not the answer.

Every artefact of the increment said *escape*. The fix is an escape function. The tests are named
for round-tripping. The docstring's "region this cannot reach" paragraph names TOML *positions* —
literal strings, bare keys, numbers — and no *values* at all. The battery's six rows each removed
one escape and watched a test die. Six mutants, six kills, and the whole apparatus was blind in
the same direction, because **the question it was built to ask was "is this escaped correctly",
and the answer for this class is "there is nothing to escape it to".**

The check that would have caught it is one question asked before the fix, not after: **what is the
set of values this promise is over, and does every member of it have an image?** Enumerating the
domain is a different act from testing the function. Eleven values were chosen for the corpus, all
of them representable, by people looking for hard-to-escape characters.

### The refuter was right about the mechanism and wrong about the disk

The reviewer that found this rated it medium. Its stated reason: *"the crash happens before that
file is written, so this does not brick the target directory — a retry with a valid name
succeeds."* Both halves are false. `Path.write_text` opens and truncates, then encodes, so the
zero-byte file is already there when the encoder raises; and the retry is refused.

The refuter reproduced the traceback and reasoned from it to a state it never looked at — `ls` and
`wc -c` were one command away. **This repository's recurring failure has a shape, and this is it:
a valid inference over a population nobody enumerated.** The judge ran the command and overturned
the severity upward, which is the only reason it was not landed as a medium.

### Making a value legal relocates the question; it does not answer it

A second finding from the same review, measured and confirmed: `pnk budget` prints `kb.name` raw,
so a name carrying an ANSI escape reaches the terminal as a live escape sequence, and a name
carrying a newline breaks `render()`'s one-entry-one-line contract with no error anywhere.

Before the fix, such a name bricked the KB, so nothing downstream ever saw it. **Escaping *for
TOML* discharges the obligation TOML has, and discharges nothing that a terminal, a filename, a
log line or an HTML page has.** The moment a class of input stops being rejected, every consumer
of that value inherits a question it was never asked — and none of them changed, so none was
reviewed. The increment's own tests cannot see this by construction: they assert the value comes
back out unchanged, which is exactly the property that delivers the bytes downstream.

The check is cheap and was not run: **who reads this value now, and what does each of them assume
about it?** Here that is one grep and twelve call sites — eleven are JSON payloads or in-memory
comparison, and `budget/summary.py:193` is the single plain-text consumer.

One correction worth keeping, because the narrower claim is the defensible one: the review called
this *previously unreachable*. It was not — a hand-written manifest carrying `\u001b` always
parsed and always printed raw, on `main` too. The fix changed the **route**, from *hand-edit your
TOML* to *pass a flag*. A widening, not a creation.

### Code no test can pin, found by a count that came out wrong

The judge proposed excluding `bool` from the new allow-list: `isinstance(True, int)` is `True`,
and `str(True)` is `True` where TOML's literal is `true`. It was built, and a test was written for
it, and both were removed — because the escaper **escapes content and never adds quotes**, so a
bool renders `True` from either branch: bare at `dim = {{ embedding_dim }}`, and inside the
template's own quotes at `name = "{{ name }}"`. The exclusion had no observable effect at any
interpolation in the file.

What exposed it was not review. The fragment claims a red/green split, so the split gets measured
by removing the hook and running the file. It came out **5 green** where the four controls were
known and named. One line of arithmetic, and the fifth green test was the new one — passing
without the fix it was written to pin, with a battery row that would have survived. **The
arithmetic was the instrument; nobody read the test and saw it.**

### The review harness said "found nothing" when nobody had looked

The third adversarial pass over this increment returned, in its own words, **"PASS FOUND NOTHING
that survived refutation"**. All four of its lenses had stalled and errored; `agents_done` was
**0**. The verdict string was mine — the script tested `survived.length === 0` and never asked
whether anyone had looked, so a vacuous run and a clean run left by the same exit.

Pass 1 had already shown the softer version: *8 raised, 4 confirmed* while five of its fourteen
agents were dying on a session limit, one whole lens never running, and two findings never
refuted — one of which was the only real code defect in that pass. **Truncation is not random
with respect to value**: a lens that reads text finishes first, and a lens that must build a
fixture and run a command reports last, so the expensive lens is first to be cut and it is the
one that finds behaviour.

The fix is structural, not a habit: the harness records which lenses actually returned and reports
**VACUOUS / PARTIAL / CLEAN** rather than a count. A count cannot carry the difference, and asking
a human to read the error list first is asking them to distrust the summary they were given.

Which is the same lesson as [this increment's earlier
one](#a-mutant-killed-for-the-wrong-reason-is-a-survivor-wearing-a-green-light-20260902-1159)
arriving from the opposite direction: there, the aggregate was clean and the kill *reason* was
wrong; here, the reason would have looked fine and the *count* was wrong. **Keep a number in the
fragment that has to be re-derived.** It is the cheapest adversary in the repository.
