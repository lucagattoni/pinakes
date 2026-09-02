- **A KB name containing a quote, a backslash or a control character bricked the KB at creation,
  silently (S4).** `pnk init --name 'Bob'\''s "Special" KB'` exited `0` and printed *created*, and
  the `pinakes.toml` it wrote was not TOML — `name = "Bob's "Special" KB"`. Every later command
  then failed, and `pnk init` refuses a directory that is already a KB, so **the remedy surface was
  empty**: recovery meant hand-editing the manifest. No flag was needed to reach it — `init` falls
  back to the directory's own name, so a folder called `a"b` was enough.
- **Fixed at the mechanism, not at the flag.** `template._render` now passes a `finalize` hook to
  the Jinja template, so *every* `{{ … }}` is escaped for the TOML basic string it lands in, and the
  next template variable that carries user text inherits it without anyone remembering to. Escaping
  follows TOML v1.0.0: `"`, `\`, `\b`, `\f`, `\n`, `\r`, and `\uXXXX` below U+0020 and at U+007F.
  **A tab is deliberately left raw** — it is the one control character a basic string may carry, so
  escaping it would rewrite a legal byte. Non-strings pass through untouched, which is what keeps
  `dim = {{ embedding_dim }}` a bare integer rather than an unreadable `"384"`.
- **What it does not cover, stated in the file rather than implied.** Escaping makes a value safe
  inside a *basic* string. It cannot make one safe inside a TOML literal string, or bare into a key
  or a number. Every variable this build supplies lands in a basic string except `embedding_dim`,
  which is never user text — so the promise holds because of what the shipped template looks like,
  not because anything asserts it. Closing that region needs a check that does not go through the
  escaper, and is its own increment.
- **Added:** `tests/test_template.py` — 29 tests over the eleven characters the sweep named, end to
  end through `load()` as well as at the render. **Four of them assert that nothing changed** and
  pass without the fix on purpose: over-escaping is the direction the obvious fix fails in, and a
  test that only proves the escaper fires cannot catch it. Removing the hook turns 25 red and leaves
  exactly those four green.
