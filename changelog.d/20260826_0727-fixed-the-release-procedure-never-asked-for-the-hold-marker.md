- **The release procedure now asks for the hold marker, which is why the marker had never once been
  produced by following it.** `docs/RELEASING.md`'s release-sweep table names every place a release
  stales, and its `docs/STATUS.md` line 3 row said only *bump it with `__version__`*. But
  `__version__` means *landed on `main`*, not *published*, so between the release commit and the
  version reaching PyPI that line names a version `pip install` cannot get — **on a page that
  deploys on every push.** The row now carries the marker's shape, the version it must name, when it
  is removed, and the rule that its qualifier **names the index and never the tag**. The marker was
  **0-for-2** on being produced by the procedure, and the procedure is the reason.
- **`docs/STATUS.md`'s own hold marker said *"NOT tagged"*, which is a claim about git rather than
  about the index.** It goes false at `git tag` while the version is still unpublished, so the line
  would have been half-wrong for the whole interval between tagging and publishing — with
  `tools/status_header_gate.py` green over it, because layer 2 requires only `⏸` plus a bold span
  naming the published version. The qualifier now names the index alone. **The gate was driven red
  on purpose to confirm it sees the marker at all** — exit 1 with the marker removed, exit 0 with it
  restored.
