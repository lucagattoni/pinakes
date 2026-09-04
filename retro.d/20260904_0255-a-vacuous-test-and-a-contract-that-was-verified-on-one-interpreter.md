## Row 38 — a test that proved nothing, and a contract "verified" on one interpreter (20260904 02:55)

**HIGH — a test can stop testing anything without ever going red, and the only way to know is to
disable its instrument and watch it still pass.** `test_an_unreadable_linked_kb_path_is_a_warning_not_a_traceback`
monkeypatched `Path.is_file` to raise, and asserted that `pnk doctor` reported a WARN. Its fixture
built the partner directory **without a `pinakes.toml`** — so the WARN it asserted came from the
partner genuinely not being a KB, and the injected `PermissionError` decided nothing at all. I did
not infer this: I disabled the `monkeypatch` line and re-ran, and the test passed unchanged. It had
been green for the wrong reason, and no gate anywhere can see that, because a vacuous test and a
sound one are the same colour. The replacement uses a real, synced partner KB behind a real
`chmod`, so the permission is the only thing that can make it fail.

**HIGH — "verified" in a docstring is a claim about the machine it was run on.**
`why_not_a_kb`'s docstring argued that it *may* raise and that its callers guard it, naming
`exists()`, `is_symlink()` and `is_dir()` as raising on an unreadable parent, and marked that
**verified**. It was verified on one interpreter. On 3.14 those calls return `False`, so nothing
raised, no `except OSError` fired, and three commands printed *"no such directory"* about a
partner on disk. The docstring did not merely go stale — it was **load-bearing**, because three
call sites carried comments justifying their guards by pointing at it. One sentence measured once
propagated into three modules.

**MEDIUM — the argument against a total contract was the thing worth re-reading, not the code.**
That docstring gave an explicit reason it could not be total: there is no answer it could return
for *"I could not tell"* that a caller would not have to branch on anyway. That was false the whole
time, and its own callers proved it — every one of them was already printing `exc.strerror`, which
is exactly the answer. The same module argues the general case twelve hundred lines up, in
`resolve_path`: a function three call sites each had to remember to guard is a function with the
wrong contract. **The counter-argument to a rule was sitting in the same file as the rule.**

**MEDIUM — the same seam failed for the fifth time in one increment.** Five tests faked
`Path.is_file` because that was the spelling the production code happened to use. Each went red the
moment the call moved to a version-independent one — which is the *loud* failure. The quiet one had
already happened: on 3.14 the real call raises for neither errno these tests name, so the branch
each certified was dead while the fake entered it and they passed on both interpreters. **Fake the
OS boundary, not the caller's spelling of it.**
