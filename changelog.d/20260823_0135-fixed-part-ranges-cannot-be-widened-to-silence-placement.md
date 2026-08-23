- **The placement check can no longer be switched off by editing the heading it reads.** Part ranges
  are read out of `docs/ROADMAP.md` — the document the check polices — so appending
  ``— `0.8.0` onward`` to `# Part 5 · What is not built` made a release section filed under it
  "correctly placed": twenty characters, exit 0, and the only trace was a green report line changing
  `holding no releases: Part 5` to `holding no releases: none`. Two Parts may now not claim the same
  versions, and the Parts must ascend with the document — `# Part 4` declaring `0.8.0` onward is
  what stops `# Part 5` doing so. Separately, the Part floor was **four** against a real count of
  **five**, so demoting `# Part 5` to `## Part 5` passed it exactly while handing every section
  beneath to Part 4, whose range holds everything; the floor is now the real count.
