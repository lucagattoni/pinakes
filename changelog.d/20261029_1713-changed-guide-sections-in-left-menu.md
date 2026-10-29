- **The docs site's left menu now lists the Guide's sections.** "1. Guide" is one page, so unlike
  "2. Reference" and "3. Concepts", which open onto their pages, it had nothing to expand and its
  sections appeared only in the right-hand column. `docs/stylesheets/chapter-sections.css` shows
  the section list that Material already renders inside that menu entry, for a single-page chapter
  other than Home, from 76.25em upward where the left menu is a permanent column. Only the
  top-level sections are listed; the right-hand column is kept and still holds the whole tree, and
  narrower screens keep Material's drawer as it was. It is a stylesheet and no script, and
  `GUIDE.md` is untouched, so its anchors and its GitHub rendering do not move. Checked in a
  browser at 1741, 1300, 1219, 1000 and 520 px (dark, and light at 1300) and across instant
  navigation; `mkdocs build --strict` exits 0.
