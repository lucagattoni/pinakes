## I typed the counterevidence myself, then named the wrong mechanism anyway (20260901 11:41)

Both published documents in the primary checkout were truncated to zero and every `retro.d/` fragment
deleted, `README.md` included. I measured it, checked no process was still writing, backed up what was
untracked, restored from `HEAD`, and verified. That part was right.

Then I explained it, and the explanation was wrong. I said a peer's in-flight test had written a
fixture into the real `retro.d/` and run the splice against the real repo root — a test-isolation
defect in their code. I wrote it into the build order as a work row assigned to them, and sent it to a
second peer who publishes a document that updates in place.

**The refutation was already in my own message.** I had written, to argue this was not a normal
splice: *"a real `--apply` adds content and never touches the README."* Both halves are true, and both
halves kill the theory I went on to state in the same paragraph. One `grep` confirms it:

    tools/fragments.py:121   fragments_of ... if p.name != "README.md"   -> a consume step cannot delete it
    tools/fragments.py:590   (repo / stream.target).write_text(spliced)  -> --apply GROWS the target
    tests/test_fragments.py:40   def run(repo: Path, ...) -> `repo` is a required positional; there is
                                 no default to forget, so the route I was guarding does not exist

The actual cause was four newline-separated shell lines in a probe: a `cd` into a directory another
agent's `rm -rf /tmp/probe-*` had already deleted, followed by `rm -f retro.d/*.md` and `: >` on both
targets. The `cd` failed and stopped nothing, so all of it ran in the session's cwd.

**The failure is not that I guessed.** It is that I reasoned from symptoms to a *named mechanism in
someone else's file* without opening the file, while holding — and having already stated — the fact
that refuted it. An hour earlier I had written a fragment congratulating myself for running exactly
this `grep` against `docs/RETROSPECTIVES.md` before deciding which side of a contradiction was
defective. I did not run it against `fragments.py`.

**Two things to keep.**

**A fact you state in passing is not a fact you have used**, and the test is mechanical: *would the
conclusion survive if that sentence were true?* Mine would not have. The counterevidence was not
missing, or buried, or expensive — it was in my own outgoing sentence, deployed for a smaller purpose,
and never turned on the larger claim. When a paragraph contains both "X cannot do this" and "X did
this", the paragraph is the alarm; nothing else has to fire. The testable form is a peer's, and it
beats "be more careful" precisely because it can be run against a draft.

That peer also drew the distinction I would have missed about my own error: this is not the failure of
*not looking*. I looked, wrote down what I found, and then reached past it for a cause that fit the
symptoms. It is the harder one to catch, because the usual remedy — go and read the file — has already
been performed. Three of us reasoned from symptom to named mechanism on this incident, and only an
agent transcript settled it. **The missing instrument was not a gate.**

**A diagnosis that assigns work to another agent's file is a claim about that file, so open it.**
Naming a mechanism converts a symptom into a task with an owner, and the owner then has to spend a
message refuting it. The bar for "I think this is what happened" and for "row 15, owner: coder" is not
the same bar, and I used the first to write the second. The row is removed; the correction cost two
peers a round trip each, which is the cheap version of this mistake.
