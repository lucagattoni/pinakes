## Open corrections 1 and 3 — a guard can route a failure into a *wrong* message (20260810 01:29)

**HIGH — turning a traceback into a `PinakesError` moved the failure into a handler that already
existed and said the opposite thing.** Item 3's whole content is *stop these five reads escaping as
tracebacks*. Doing it made `describe` raise `TemplateError` — and `doctor.py` and `upgrade.py` both
already wrapped their `describe` call in `except PinakesError`, answering it with **"is not
installed here"** and a remedy about installing the template. That arm was correct while the only
thing reaching it was a template genuinely absent; a *damaged* install had been going straight past
it as a traceback. So the fix silently recruited a handler written for the opposite case, and a user
whose `template.toml` was unreadable would have been told to install a template sitting right there.

**A traceback is loud and a wrong sentence is quiet, so this is a downgrade that reads as an
upgrade.** Both surfaces reported `WARN`, both exited 3, every test stayed green — the increment's
own tests included, because they assert the *new* messages and the pre-existing ones assert the
absent-template case that still works. Nothing was red. It was found by asking who else catches
what this function now raises, which is a different question from *does my change work*.

The correction is `TemplateNotInstalledError`, a subclass so that every existing `except
TemplateError` keeps working, with `_unknown` as its only raiser and the two callers splitting the
arms. Both surfaces get their own test, because the wording is a fact with one home but the routing
is a decision each caller takes for itself — one test would leave the other free to merge the cases
back.

**Generalises past exceptions: widening a type is an interface change on every `except` upstream.**
The grep that finds it is not for the function being changed but for the *type* it starts raising,
and the question is whether each catcher's answer is still true for the new cause. `PinakesError` is
caught in 30-odd places here precisely because it is the type that means *print this and stop*, so
anything newly raised as one inherits whatever those handlers already say.

**Second, smaller, and mechanical: `git checkout -- <file>` during a mutation pass deletes the fix
being verified.** The pass ran before the commit, so restoring after each mutation restored to
`main` — three mutations in, both source files were back to their unfixed state and the tests were
"failing correctly" against no fix at all. The evidence was still true and the work had to be typed
again. **Commit, then mutate**: `BUILDING.md` orders the steps that way, and this is the reason
rather than a convention.
