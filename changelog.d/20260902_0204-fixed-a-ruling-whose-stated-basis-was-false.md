- **A ruling's stated basis was false, and both rows resting on it are corrected.** Build-order rows
  17 and 18 justified treating one fragment-gate fix as in-scope, and a second as new process, by
  the claim that `changelog.d` **already gates a fragment's filename prefix**. It does not — it
  gates the **category**, and the case that separates them is `fixed-a-thing.md`, which carries no
  prefix at all, has a category for its head, and is **accepted**, while `banana-a-thing.md` is
  refused. A malformed prefix is refused there only incidentally, by shifting the first token out of
  the six allowed categories. Nothing in this repo gates a prefix's format. The claim came from
  reading the category arm's error text — which names the whole naming convention — as evidence of a
  prefix arm, without ever testing the one fixture the two hypotheses disagree about.
- **Both rulings survive on a discriminator that does not depend on the sibling.** The question is
  whether a check enforces the **decided property** or a **different** one. A gate whose subject is
  *the stamp is the filename's* states a copy relation, so closing an exemption that one substituted
  character triggers implements that gate rather than extending it; calendar validity is a different
  property and stays deferred. The superseded discriminator — *does the sibling already do this* —
  is struck from both rows.
- **The narrowing rule itself is widened on evidence, and its stated residual was the wrong string.**
  It now exempts only a stem that does **not begin with a digit at all**, rather than one not
  beginning with eight. `2026090_0710-x`, named as the residual, is already refused today by the slug
  arm, because a failed prefix strip leaves an underscore in the stem and the slug pattern forbids
  it; the real residual was the all-hyphen shapes, which the wider rule leaves none of. Measured over
  all **310** fragment paths that have ever existed: of the **52** carrying no canonical prefix,
  **none begins with a digit** under either form, so the wider rule costs nothing historically. Its
  one real cost is named rather than left to be discovered — a name like `5-lessons.md` becomes
  refused, which is correct, since every new fragment owes a prefix.
