## The assembled document nobody reads, and an extent computed after it was destroyed (20260823 16:18)

**HIGH — a defect can exist only in the assembled document, where no instrument is pointed.** Five
blocks of `---` / `category: <x>` / `---` survived a splice into `CHANGELOG.md` and
`docs/RETROSPECTIVES.md`. They are not inert: `---` after a **text** line is a setext underline,
not a thematic break, so each rendered as **an H2 titled with its own metadata** — and two of them
have been served from the published site with live permalink anchors. **Every gate was green.**
`mkdocs build --strict` resolves links and a spurious heading is not a broken link;
`tools/markdown_link_gate.py` reads link targets; and the new fragments document-gate reads **ATX**
headings, so setext is outside it by construction. Three instruments aimed at these two files, and
the defect sat between all of them. The same shape as the item closed hours earlier —
`fragments.py --check` validating what it reads and never what it writes — which is the tell that
the *class* is the assembled document, not any one checker.

**MEDIUM — a bottom-up edit destroys the markers a top-down extent depends on.** The repair had to
delete each residue *and* re-bullet the entry it preceded, so each entry's extent ran from the
residue to the next structural marker. Deleting bottom-up is the standard way to keep earlier line
numbers valid — and here it was wrong, because **a later residue is an earlier entry's stop
marker**. The first pass deleted it, the extent then ran on into the following entry, and the result
indented a top-level changelog entry into a nested sub-item of its predecessor. **Nothing failed.**
No assertion fired; the residues were gone and the spurious headings were gone, so every check the
repair had written for itself said yes. It was caught by reading the rendered structure afterwards
and seeing one `NESTED!` where a `BULLET` belonged. **Compute every extent against the untouched
document first, then apply.** And the older rule that would also have caught it: *read the diff an
edit produces, never its anchor.*

**LOW — the count was five and the record said three, because the record counted one stream.**
`tools/fragments.py`'s docstring named three residues in `CHANGELOG.md`. There were also two in
`docs/RETROSPECTIVES.md`, missed because the note was written from the refusal that motivated it,
and that refusal is changelog-shaped. **A count taken from the thing that prompted the search
inherits the search's scope.**
