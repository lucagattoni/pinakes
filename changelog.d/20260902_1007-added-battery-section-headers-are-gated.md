- **A battery's section header is now gated against the two forms the README reserves.**
  `tools/batteries/README.md` reserves `X.Y.Z · ` for a property that has shipped and
  `unreleased, YYYYMMDD · ` for one that has not, and nothing checked it — so a section could name
  neither and the directory would still read as a record of which release made which property true.
  `tests/test_batteries.py::test_every_section_header_names_the_release_it_belongs_to` refuses a
  third form, and the directory-built-to-break-it control carries a non-conforming header so the
  check is shown able to fail rather than assumed to work.
- **Fixed a section header that named neither** — `src-pinakes-pairing.toml` carried
  `# unreleased, 20260831 - …`, a hyphen where the `·` separator belongs. It is the second such
  header, and it survived the audit that found the first because that audit's selector required
  the `·` the offending line was missing.
