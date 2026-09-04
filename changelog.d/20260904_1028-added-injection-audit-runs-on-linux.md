- **The vacuous-injection audit now runs on Linux, and says which environment it ran in.**
  `.github/workflows/injection-audit.yml` runs `tools/vacuous_injection_audit.py --runs 2` on
  `ubuntu-latest` under the declared floor, 3.13, asserting the interpreter it actually got and
  taking another as a `workflow_dispatch` input.
  It exists for one question a macOS checkout cannot answer about itself: an injected
  `ENAMETOOLONG` is redundant where a real 300-character filename raises it and load-bearing where
  it does not, and that is a property of the filesystem, not of the code. The report now names the
  interpreter, the platform and `NAME_MAX` beside its counts, because a verdict of that kind is a
  claim about an environment.
- **Three ways the audit could report success while measuring nothing are now refusals.** An empty
  site list is refused rather than printed as `0 sites · 0 vacuous · 0 not ruled` (`--min-sites`,
  default 10); a probe run in which nothing passed is `INCONCLUSIVE` rather than a verdict, so an
  all-skipped selector is no longer reported as a vacuous fake; and a run whose environment changed
  between its first and last probe is `UNATTRIBUTABLE` and exits non-zero. The exit status now
  carries the *unruled* set and still exits 0 on a `VACUOUS` row, which is a finding for a person
  to read rather than a build to fail.
