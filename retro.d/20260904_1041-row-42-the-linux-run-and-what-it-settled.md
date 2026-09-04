## Row 42 — the Linux run, and the prediction it confirmed (20260904 10:41)

**The run happened, and it matched the prediction exactly.** `injection-audit` run `33864216950`,
on `main` at `e3d82dd`, `ubuntu-latest`:

    15 sites · 1 vacuous · 0 not ruled
    probed under Python 3.13.15 on Linux 6.17.0-1022-azure (x86_64), NAME_MAX=255.
      VACUOUS   test_cli_link.py:617  monkeypatch.setattr(os, "stat", name_too_long)

**Byte-identical to both macOS runs** — same count, same single site, same unruled total. Fifteen
predictions were written down before it fired (fourteen `sound`, one `VACUOUS` at `:617`, none
judged platform-dependent) and **fifteen of fifteen held**. That is worth stating plainly because
the alternative outcome was equally prepared for: the prediction named what would falsify it, and
nothing did.

**What it settles.** The `ENAMETOOLONG` injection is redundant on **both** platforms, so the test's
own comment — *"Redundant on this machine and load-bearing on CI, which is why it stays"* — is
**superseded rather than wrong**, and it is corrected in place rather than deleted. What changed is
that it describes the **pre-refactor** code path, which reached the filesystem through
`Path.is_file()`, where 3.14 swallows `ENAMETOOLONG` so the guard never fired.
`paths.unreachable_through_links` did not exist when that comment was written; production now calls
`os.stat` directly, twice, so the errno survives to the message on both platforms. **Deleting the
sentence would have deleted the reason** — the same failure mode as every other silently-corrected
claim recorded this week.

**A second thing the run made visible, which no macOS run could have.** The fake raised
`OSError(63, "File name too long")` — **63 is macOS's `ENAMETOOLONG`; on Linux it is a different
errno entirely.** The assertions never caught it because the message is supplied explicitly, so the
fake simulated the wrong condition while saying the right words. It is now
`errno.ENAMETOOLONG`. **A fake is a claim about a system, and a hard-coded errno is that claim
written in one platform's dialect** — invisible until the test runs somewhere else, which is the
same shape as the verdict this row went to Linux to obtain.

**What is deliberately NOT done, and why.** The fake now decides nothing on either platform that has
been measured, so whether it should exist at all is a live question. **It is not taken here:**
development is paused, and removing an injection changes what the test *exercises*, not merely what
it *says*. The evidence for taking it is in the comment at the site and in run `33864216950`; the
evidence against is that neither platform has been shown to be the only two that matter.

**On the instrument, since this is the run that used it.** The environment line did its job on its
first real outing: `NAME_MAX=255` appears beside the counts, and it is the exact quantity that
decides the one verdict in the report. A reader a year from now does not have to know what
`NAME_MAX` was on an Azure runner in September 2026 — the report says so.
