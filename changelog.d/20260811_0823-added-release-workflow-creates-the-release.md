- **The release workflow creates the GitHub release.** It never had a step that did — `git log -S`
  confirms none ever existed — while `docs/RELEASING.md` step 8 said to create it by hand and
  `docs/STATUS.md` recorded doing so as a *recurring workflow failure* six times running. The job's
  `success` was honest each time; it did everything it was asked to. `gh release create
  --verify-tag --notes-from-tag` now runs **after** the PyPI upload, so a failure there can never
  cost a release its version number — PyPI refuses a version twice.
