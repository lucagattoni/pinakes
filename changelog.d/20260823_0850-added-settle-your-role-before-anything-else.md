- **A cleared context settles its own role, and its peers', before it writes anything.** New rule at
  the head of `CLAUDE.md`, with the procedure and the failure record in
  [`docs/BUILDING.md`](https://lucagattoni.github.io/pinakes/BUILDING/#settle-your-role-before-anything-else):
  take your role from what the **user** said in *this* session — never from the repo, the previous
  session, or the work in flight — ask every live peer theirs, and **if you cannot determine it,
  ask and block**. It is stated as a blocking exception because § *Working mode — autonomous by
  default* otherwise overrides the default of stopping. Both failure directions are silent and both
  happened on 20260823: a session that opened on an unlanded docs branch would have inferred
  *planner* and landed documents it did not own, and a session that assumes *coder* leaves a
  document wrong out of misplaced deference.
