## Row 32 — a ruling that was wrong on a premise, and a fake that outlived its branch (20260904 02:02)

**HIGH — a decision can be wrong because of a fact, and the fix is to measure the decision, not to
re-argue it.** The plan ruled `paths.unreachable` as the discriminator for both of this
increment's fixes, and stated that it would "restore 3.14 to what 3.13 already does". It would not.
`unreachable` is `lstat`-based, so on a symlink pointing into an unreadable directory it answers
`False` on **both** interpreters. Building the ruling as written would have left 3.14 broken *and
regressed 3.13*, moving that document from `paid extraction unreadable` into neither list —
silently dropping a row 3.13 reports today, on the very shape that produced the ULID-deletion bug.
The obvious repair over-fires in the other direction: a naive `os.stat` sibling answers `True` for
a symlink loop, where 3.13 answers `False`. Neither candidate alone is parity. What settled it was
a table of seven shapes on two pinned interpreters, with the controls — absent, dangling, loop,
ordinary file — in the same run as the cases. **The ruling was re-ruled within the hour on that
evidence.** The cost of measuring first was about twenty minutes; the cost of not doing it was a
regression on the interpreter this project declares as its floor.

**HIGH — a fake pinned to an implementation detail fails loudly when the detail moves, and goes
silent when the detail's *behaviour* moves.** `test_an_unreadable_directory_is_refused_rather_than_
crashing` monkeypatched `Path.is_file` to raise, and passed on both interpreters — while on 3.14
the real `Path.is_file()` raises for **neither** errno the test's own comment names, so the
production branch it certified was dead. The test was measuring its own fixture. When the fix moved
the call to `paths.unreachable_through_links`, the same test went red immediately, because the fake
no longer intercepted anything. **Both failures are the same seam; only the noise differs**, and
the quiet one had been shipping. The repair was to move the fake down to `os.stat`, the OS
boundary, and to add a real `chmod` test beside it — the injected one now earns its place on the
errno no permission fixture can produce and on running as root, where the `chmod` fixture skips.

**MEDIUM — "the library does X" is often a measurement of one interpreter, written up as a fact
about the library.** The docstring being fixed here claimed `pathlib` "ignores `ENOENT`, `ENOTDIR`,
`EBADF` and `ELOOP` … but nothing else". True on 3.13, and on 3.14 `Path.is_file()` swallows
everything, `EACCES` and `ENAMETOOLONG` included. That single sentence is why an `except OSError`
clause sat dead in production and why a test sat green on top of it. The replacement constant is
named for **what 3.13 does**, not for what pathlib is believed to do, and its four members were
measured on both interpreters rather than read out of CPython — with the one member whose fixture
is not portable marked as measured-but-not-pinned instead of quietly asserted.

**MEDIUM — an audit's list decays, and one of these had already been fixed by a neighbouring
branch.** Of the survivors this row carried, `doctor.py:411` was cured in `514fe46` — row 31's own
commit, in passing — while the row still described it as live and named the release that had walked
past it. Checking `git log -S` on the exact line took a minute and removed an item from the queue.
An unverified finding ages in both directions: it can be worse than raised, as the `link` one was,
or already gone.
