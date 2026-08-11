- **`pnk sync --rebuild` re-chunks a paid-extracted document instead of copying its chunks
  verbatim, whenever its extracted text is still cached.** A `[chunking]` edit — `headings`,
  `max_tokens`, `overlap` — never reached a paid document, while the run stamped the current
  settings over the whole index: an index claiming a chunking it did not have. The extraction cache
  lives under `.pinakes/` and **survives a rebuild**, so the text is read back and re-chunked
  without paying to extract again.
- **When the cached text is gone, the chunks are kept and the index says so.** Re-extracting costs
  money and `--rebuild` is the remedy `pnk doctor` prints, so this path never spends: the run names
  each document it could not re-chunk, the index records how many exceptions it carries, and
  `pnk doctor` reports *"index matches the configured chunking, except N paid document(s) carried
  forward"* — **OK with a note, not a warning**, because nothing is broken and the only remedy
  costs money.
