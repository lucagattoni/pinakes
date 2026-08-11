- **`pnk init` validates a template's declaration before it creates anything.** A template whose
  `files = [...]` is refused — it names `_versions/`, writes outside the KB, or reads outside the
  template — used to raise *after* `pinakes.toml`, `docs/` and `.gitignore` had been written,
  leaving a directory that is almost a KB and that a second `pnk init` then refuses *as* one. All
  three checks now run before the first byte, so a refusal leaves no directory at all. The
  guarantee is **validated before writing, not atomic**: a symlinked ancestor of the target can
  still change between the check and the write. `--ci` has behaved this way since its own refusal
  was moved; this makes the guarantee uniform.
