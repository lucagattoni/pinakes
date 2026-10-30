- **A GitHub release's notes are the tag's annotation, not the merge commit's subject.** `release.yml`
  creates the release with `gh release create --notes-from-tag`, and `actions/checkout` had stored the
  tag's *commit* under the tag's name for a tag push (`git fetch --no-tags --depth=1 origin
  +<sha>:refs/tags/<tag>`, in the Release run's log), so the runner held a lightweight tag and the
  notes fell back to the commit message. Six releases were read, 0.32.8, 0.32.7, 0.32.6, 0.30.0, 0.25.0
  and 0.22.0, and all six read `Merge branch '…'`; the other 29 of the 35 tags from 0.22.0 to 0.32.8
  were not read. A new step, `Restore the tag's annotation`, right after the checkout fetches the tag
  object over the flattened ref (`--force`, or git refuses with *would clobber existing tag*) and exits
  1 unless the object is an annotated tag with a subject. It runs in front of `uv publish`, where a
  failure costs a deleted tag and not the version number, and it refuses a lightweight tag and an empty
  annotation a second time after `make release-check` did. **0.32.8's own notes were backfilled** from
  its annotation with `gh release edit`; the older five were left as they were. Tests run the
  workflow's own `run` text against a clone made the way `actions/checkout` makes one, pin that
  premise first, refuse a lightweight tag and an empty annotation, and hold the parsed workflow to
  *before the upload, unskippable, no `exit 0`*; six mutants joined the battery that claims
  `release.yml`, and a check that the placement test fails for a step moved behind the upload. **The
  fix has not run in Actions**: the first release cut after this lands is its first real run, and
  `docs/RELEASING.md` now says to read that release's body. Developer tooling — it ships in no wheel.
