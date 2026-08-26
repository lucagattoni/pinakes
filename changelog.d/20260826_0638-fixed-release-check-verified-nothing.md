- **`make release-check` now gates the tag instead of printing it.** Its recipe was three `echo`s —
  it read `__version__`, printed it, printed the tag, printed the command to run — with no
  comparison and no failure path, so it could not fail and therefore verified nothing, while
  [`CLAUDE.md`](https://github.com/lucagattoni/pinakes/blob/main/CLAUDE.md) sent a release operator
  to it as the last check before a publish PyPI never takes back. `tools/release_tag_gate.py`
  replaces it with four legs that can each go red: exactly one release-shaped tag points at `HEAD`
  (**absence is red** — a check reporting success with nothing to compare *is* the defect), the tag
  names `pinakes.__version__`, it is annotated with a message `gh release create --notes-from-tag`
  can read, and it is **not already on the remote** — which turns *"before the tag, never after"*
  from a convention into a check. An unreachable remote is red, never green.
- **The tag is now created before `make release-check` runs, and pushed after it.** The tag has to
  exist for anything to be compared, and until it is pushed it is a local object `git tag -d`
  removes without trace: *"before the tag"* is *before the **push***, which is the irreversible half
  and the one PyPI's refusal to accept a version twice is actually about.
