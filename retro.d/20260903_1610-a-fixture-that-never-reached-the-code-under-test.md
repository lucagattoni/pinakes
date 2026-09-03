## A fixture that never reached the code under test (20260903 16:10)

**What happened.** A peer handed over a reproduction for row 31's first shape: make the `[sources]`
root a symlink into a blocked ancestor — `kb/docs -> ../blocked/realdocs`, with `blocked` at
`0o000` — and observe that `Path.is_dir()` raises on 3.13 while returning `False` on 3.14. It came
with the interpreter divergence measured on both versions, and with a named source line. Rebuilding
it as a fixture, it never ran: `manifest._check_include_containment` refuses a root that resolves
outside the KB, so the manifest fails to load and the walk is never reached at all.

**What was wrong, and what was not.** The interpreter divergence was real. What did not survive was
everything downstream of the fixture: the reachable shape needs the symlink target **inside** the
KB (`kb/docs -> store/realdocs`, `kb/store` at `0o000`), and with that shape the 3.13 raise is at
`is_dir()` and not, as reported, one line earlier at `.resolve()` — `resolve()` is non-strict here
and does not stat. A precise, correctly-measured claim about the wrong tree.

**Why a peer's reproduction is the easy one to accept.** It arrives *already carrying* the things
that normally warrant trust: a measurement, both interpreters, a file and a line number. None of
those is evidence about whether the state it builds is reachable by the code under test, and that is
the one property a reproduction has to have. A fixture that errors before the code under test can
still print a plausible failure — a different failure — and the reading of it is confirmatory
either way.

**The check that catches it, and it is one line.** Assert something the fixture must have *reached*
before believing what it reports. Here that is the state right after the setup: the index contained
`store/realdocs/a.md`, which is only true if the manifest loaded and the walk ran and keyed the
documents by the resolved root. The test now carries that assertion with a message explaining what
it is for, rather than beginning at the failure the fixture is meant to produce. **Opening a
reproduction with a proof that it got as far as the code under test costs one assertion and is the
difference between a regression test and a fixture that would pass on an empty function.**

**What was right about the exchange.** The peer had already applied this to itself once that day —
correcting a claim of its own that was true of its fixture and false of the language — and said so
in the handover. That is what made checking the fixture the obvious next step rather than a slight.
The rule *a peer's claim is not evidence until you have checked it* survived being handed
a claim that was 80% correct, which is the hard case: the wrong 20% was load-bearing, and every
signal of rigour attached to the 80%.

**The positive counterpart, done for this increment rather than assumed.** The rule *"unit tests
prove a component honours a parameter — only running proves the parameter arrives"* is the same
statement from the other side, so the fix was exercised the way a user meets it before landing: a
real `pnk sync` over a 30-document KB with `docs/vault` at `chmod 000`. It printed
`failed: docs/vault: directory could not be entered: Permission denied.` with the remedy,
`0 removed` and `30 unchanged`, and **exited 1**; `pnk doctor` then exited 0 with nothing to say
about orphans or retired rows, and `pnk search "appraisal criteria"` answered **from the held
document inside the locked directory**. Every one of those is asserted by a test as well. The run
is what shows the assertions are about the command the user types.
