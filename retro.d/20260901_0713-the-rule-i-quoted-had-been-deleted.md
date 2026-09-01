## The rule I quoted verbatim had been deleted a minute after I started (20260901 07:13)

**HIGH — the file you are told is authoritative is a copy, and the copy has no clock on it.**

I settled a disagreement with a peer by quoting the governing rule out of `~/.claude/CLAUDE.md`. I
quoted it verbatim. I read the surrounding argument. I said which clause carved out my case and why
the peer's narrower reading was not what the sentence said. Every discipline this repository has
written down for quoting a source, I applied — and I was wrong, because **the sentence had been
deleted 40 minutes earlier.**

| | |
|---|---|
| My session started | 20260901 **07:00** UTC |
| `~/.claude/CLAUDE.md` last modified | 20260901 **07:01** UTC (`TZ=UTC stat -f "%Sm"`) |
| What my system prompt held | the text as of 07:00 |
| What was on disk | its replacement, ruling my case the other way, *deliberately* |

**The injected `CLAUDE.md` in a session's context is a copy, and the copy has no knowable age.** The
old text read *"it does not cover a lone adversarial reviewer judging one finding on its merits"* —
which reads as a per-finding carve-out, and I built a fan-out of eleven top-tier judges on it. The
user had replaced it that minute with a clause naming exactly that case and ruling against it: *"a
lone reviewer ruling on a single finding on its own merits **is** a refuter, not the judge — then
**one Opus pass** over the refuters' collected verdicts."* The new sentence exists *because* the old
one was ambiguous. I found the ambiguity and resolved it in the direction that had just been closed.

**The first version of this entry said the copy "never refreshes". That is false, and the truth is
worse.** A peer holding the *post*-edit text in its own injected block corrected it, and both halves
are checkable on this machine within the same hour:

| | My session | The peer's session |
|---|---|---|
| Injected copy holds | `Audits and large analyses ALWAYS run on Sonnet 5` | `env.CLAUDE_CODE_SUBAGENT_MODEL … verified 20260901 07:00 UTC` |
| That string on disk | **no match** — the heading is gone | present — it is the 07:01 replacement |
| Vintage | pre-edit | post-edit |

Same file, same machine, same hour, **two live sessions holding different vintages, refreshed on a
trigger neither could observe.** Not "old session, old copy" — my start time did not tell me my copy
was stale, and the peer's would not have told it that its copy was fresh. Nobody has isolated the
trigger and this entry does not guess one.

**This is not the relayed-claim failure this repo already has three instances of.** Nothing was
relayed; I read the primary source. It is one layer under that: the primary source I read was a
cached copy of the primary source, of indeterminate age. The rule that falls out is narrow and cheap,
and the *reason* is what the correction changes:

> **Before quoting `CLAUDE.md` to settle a dispute, `grep` it on disk** — not because a long session
> is likely to be stale, but because **no session can determine from the inside whether it is.**

The peer caught it by grepping the file; I had not, because I believed I was already looking at it.

**Two things I did right and one I did not.** I stopped the run rather than let the fan-out spawn,
edited the stage out, and resumed from the run id — the eleven measure and eleven refute legs were
already explicit `model: 'sonnet'` and cached, so the cost was the eight legs in flight. I did not
check the file before asserting from it, and in the same message I raised *a sound argument over an
unexamined domain* against the peer's cost table — whose scope was stated in the message and one
grep from confirmable. **Invoking the rule is not applying it**, and I was the one not applying it
while naming it.

**The resume geometry, since it is not obvious.** Workflow resume caches on `(prompt, opts)`, so
editing a late stage leaves earlier legs cached and free. But a stage gated by a `parallel()` barrier
after a `pipeline()` spawns milliseconds after the last leg returns — there is no window to "let the
fan-out finish, then kill before the next stage". With a barrier the choice is *stop now and lose
what is in flight*, or *let it complete*. Which of `pipeline` and `parallel` gates the stage decides
whether a zero-waste edit exists at all.

---

**Three findings from peers this increment, verified here rather than taken on report.** Each was
handed over with a wrong cause attached, and in every case the conclusion survived and the
explanation did not — which is the argument for re-running rather than re-reading.

- **A suspiciously clean result is a reason to check the harness, not to write it down.** A peer's
  4×4 measurement matrix returned sixteen identical rows. Four programs with different argument
  parsers do not agree to the character; the uniformity was the tell, not the content. This is a
  *positive* test for harness breakage, and it sits beside the mutation rule this repo already
  has — *a run with no kills is a broken harness, not a clean bill* — discovered independently, in a
  different instrument.
- **A null result from a selector you did not validate carries no information at all.** Two
  instances, one peer, one hour. First: it grepped for a sentence, got `0`, and nearly reported
  landed work as unlanded — the sentence spans a source line-break, so the contiguous string does
  not exist even though the text does. Second: it grepped `retro.d/` for three phrases it
  remembered writing, got `0`, and was one keystroke from telling the user a landed fragment had
  been lost — **the file is named `checking-the-wrong-artifact.md` and was in the directory being
  searched.** None of the remembered phrases survived into the committed text. What caught it was
  an `ls` in the same command block printing the filename; not the grep, and not a gate.

  Distinct from the six refutations ruled against on 20260831: those failed on *semantics* (the
  string matched, the claim behind it differed); these fail on *encoding* (the claim was true, the
  string could not match). The operational form is testable where "read the surroundings" is not,
  and the second instance adds an edge to it:

  > **Prove the selector can match something before trusting that it did not** — and when searching
  > for a *document*, list the directory before grepping its contents. **A filename is a selector
  > you did not choose**, which is exactly what makes it useful.

  The asymmetry is what makes this worth the entry — a false negative on *did this land?* invites
  rebuilding landed work, and this repository has come within one message of that twice. The
  substitution half of the same family — running the right measurement against the wrong artifact,
  and why *the nearest to hand is the one that flatters* — is already recorded and is not restated
  here, in the sibling fragment spliced just above this one: *Re-running a measurement is not enough
  when there are two artifacts to run it against* (20260901 06:33). **Deliberately not a link, and the
  link was the correct form** — `#re-running-a-measurement-is-not-enough-when-there-are-two-artifacts-to-run-it-against-20260901-0633`
  resolves once both fragments are spliced, exactly as `docs/RETROSPECTIVES.md:4034` already does.
  `tools/markdown_link_gate.py` checks each fragment against its own file, so it turned `main` red at
  `b6be317`. Restore the link when sweep-plan build-order row 14 lands.
- **`uv run --frozen $cmd` cannot work in this shell, and the error message hides why.** zsh does
  not word-split unquoted parameter expansions; bash does. Measured here: `c2="python -c"; for w in
  $c2` yields **one** word under zsh 5.9 and **two** under bash. So uv is handed a single argv
  element named `python3 -c` and reports `Failed to spawn:` with the whole string as the command
  name — which reads as *that command failed* rather than *that is not a command*. **Build commands
  as arrays or `"$@"`, never as a string expanded unquoted.** Not uv-specific; it is a trap for any
  loop over commands on this machine.

**The near-miss worth recording**: that peer's first diagnosis was *"`python3` is not on the project
environment's path, only `python` is"*, and `RESUME.md` carries an instruction to use
`uv run --frozen python3`. Acting on the report would have deleted a correct instruction on the
strength of a quoting bug. `uv run --frozen python3 -c "import pinakes"` prints `0.31.1` in the
primary checkout and in a synced worktree alike. **A wrong cause with a right conclusion is more
dangerous than a wrong conclusion**, because the conclusion gets checked and the cause gets copied.
