- **A KB name containing a quote, a backslash or a control character bricked the KB at creation,
  silently (S4).** `pnk init --name 'Bob'\''s "Special" KB'` exited `0` and printed *created*, and
  the `pinakes.toml` it wrote was not TOML — `name = "Bob's "Special" KB"`. Every later command
  then failed, and `pnk init` refuses a directory that is already a KB, so **the remedy surface was
  empty**: recovery meant hand-editing the manifest. No flag was needed to reach it — `init` falls
  back to the directory's own name, so a folder called `a"b` was enough.
- **Fixed at the mechanism, not at the flag.** `template._render` now passes a `finalize` hook to
  the Jinja template, so *every* `{{ … }}` is escaped for the TOML basic string it lands in — or
  refused, where no escaping exists — and the next template variable that carries user text
  inherits it without anyone remembering to. Escaping
  follows TOML v1.0.0: `"`, `\`, `\b`, `\f`, `\n`, `\r`, and `\uXXXX` below U+0020 and at U+007F.
  **A tab is deliberately left raw** — it is the one control character a basic string may carry, so
  escaping it would rewrite a legal byte. **`int` is the whole of what passes through bare** — the
  one entry in the allow-list below — which is what keeps `dim = {{ embedding_dim }}` a bare
  integer rather than an unreadable `"384"`.
- **A value TOML cannot represent is refused, before `init` creates anything (found by review).**
  A lone surrogate — U+D800-U+DFFF — has no TOML form raw *or* escaped, and POSIX produces one
  routinely: `surrogateescape` is what an invalid UTF-8 byte in an argument or a directory name
  becomes. `pnk init --name $'kb-\xff'` used to reach `Path.write_text`, which **creates and
  truncates before the UTF-8 encoder raises** — leaving a zero-byte `pinakes.toml`, a directory
  `init` then refused as *already a KB*, and a raw traceback. **That is S4's own end state,
  reproduced by S4's own fix.** It is now a message with a remedy, raised inside `render_manifest`
  before anything is created, and the message names the code point rather than echoing the value:
  a name carrying an unpaired surrogate can carry an ANSI escape beside it.
- **The type guard is an allow-list now, not a deny-list.** It read *not a `str`*, so anything that
  was not one went out untouched — and Jinja calls `str()` on whatever `finalize` returns, so a
  `Path` carrying a quote wrote the same unparseable manifest S4 exists to prevent. No call site in
  this build supplies one; the *mechanism* claim is what made it a defect. `int` still passes bare,
  which is what keeps `dim = {{ embedding_dim }}` an integer.
- **What it does not cover, stated in the file rather than implied.** Escaping makes a value safe
  inside a *basic* string. It cannot make one safe inside a TOML literal string, or bare into a key
  or a number. Every variable this build supplies lands in a basic string except `embedding_dim`,
  which is never user text — so the promise holds because of what the shipped template looks like,
  not because anything asserts it. Closing that region needs a check that does not go through the
  escaper, and is its own increment.
- **Added:** `tests/test_template.py` — 33 tests over the **three** classes the sweep named (`"`,
  `\`, and control characters other than tab), opened out into eleven values, end to end through
  `load()` as well as at the render. **Four of them assert that nothing changed** and pass without
  the fix on purpose: over-escaping is the direction the obvious fix fails in, and a test that only
  proves the escaper fires cannot catch it. Removing the hook turns **29** red and leaves exactly
  those four green — measured by applying `finalize=None` and running the file, not counted.
- **Added:** `tools/batteries/src-pinakes-template.toml`, the first mutation battery over
  `template.py` — 9 mutants, 9 killed, run rather than inferred from anchors. It found a gap in its
  own increment's tests: the row named *a backslash is left raw* was dying on a `TOMLDecodeError`
  rather than on an equality, because **both** backslash values in the corpus carry a sequence TOML
  rejects outright — `\k` in `C:\notes\kb`, and `\a` in `C:\a"b\\c`, and it is not the same one in
  both. The quiet case — `C:\notes`, whose only sequence is the **legal** `\n`, so the manifest
  parses and means `C:` + newline + `otes` — reached no test at all. It has one now.
