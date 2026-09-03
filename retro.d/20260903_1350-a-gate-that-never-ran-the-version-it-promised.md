## A gate that never ran the version it promised (20260903 13:50)

**HIGH — `requires-python = ">=3.13"` had been a sentence in a manifest, not a tested claim, for
the life of the project.** Nothing in this repository pins a Python: no `.python-version`, no
`setup-python` step, and `uv sync --frozen` resolves to the newest interpreter available. CI's
matrix varies the *extras* — `[light]`, `[light,pdf]`, `[light,pdf,claude]` — and never the
interpreter, so every leg ran 3.14. The floor was declared in one file and exercised in none.

What it cost: `pnk sync` crashed with a raw `PermissionError` on 3.13 for a symlink into an
unreadable directory, and that crash is present in every published release tested — 0.32.2,
0.32.1, 0.30.0 and 0.25.0 all reproduce it under `uvx --python 3.13`.

**The tell was visible and read as noise.** The same commit produced a green gate and a red gate:
`./check.sh` passed in the worktree and failed in the primary checkout. That asymmetry has a note
in private memory — *worktrees get different Pythons; the primary checkout is the 3.13 outlier* —
and it was filed there as an inconvenience to route around rather than as **the project's only
instrument that ever touched the supported floor.** The one machine that disagreed was the one
machine testing what the manifest promised.

**Two rules come out of it.**

1. **A version range in a manifest is a claim, and claims get gates.** Every declared axis with a
   minimum — Python, an OS, a dependency floor — needs one leg that runs *at* the minimum, or the
   minimum is decoration. The new `minimum-python` job also **asserts** the interpreter it got
   (`sys.version_info[:2] == (3, 13)`) rather than trusting `--python 3.13` to have been honoured,
   because a leg that silently ran 3.14 would be a job going green about the one thing it exists
   to check — the same failure this fragment is about, one level up.
2. **When two environments disagree about the same commit, that is data, not friction.** The
   instinct is to make the odd one match. The question to ask first is *what is it testing that
   nothing else is*, and only then whether to align it. Here, aligning would have destroyed the
   only signal in the system.

Related: [[pinakes-worktrees-get-different-pythons]], which recorded the divergence and read it as
a hazard. It is that too. It was also the coverage.
