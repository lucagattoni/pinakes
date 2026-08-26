- **`pnk doctor` gains a `retired documents` check.** It reports any document the KB still collects
  whose id the index has retired — the document is on disk, it carries its identity, and `pnk search`
  cannot see it. `doctor` printed `sidecars: N readable` and `index: M active documents` on adjacent
  lines and compared them to nothing. The check asks about the retired **id**, never the path, so it
  finds the document where it now sits rather than where its row still says it was; and because it
  starts from a row that once existed, the sidecars the pre-commit hook mints with no index row do
  not trip it — the shipped hook pair indexes them in the same commit.
