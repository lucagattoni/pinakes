- **The release history reads in release order again.** Three ordered sequences had drifted:
  `docs/ROADMAP.md`'s release table and its per-release sections both ran
  `0.20.0, 0.22.0, 0.22.1, 0.21.1, 0.21.0, 0.20.1`, and `docs/STATUS.md`'s roadmap table put
  `0.15.1` after `0.16.0` and `0.20.1` after `0.22.1`. Every misplaced row is out of order on
  **both** readings — SemVer and release time — so no reading of the table made them right.
  `CHANGELOG.md` was checked and is clean, headings and link definitions both. The sections were
  moved as whole blocks with a script that refuses to cross a `# Part` boundary, asserts the
  rewritten file is byte-identical in length, and re-checks that every `# Part` heading still
  carries the `---` that precedes one everywhere else in the file.
