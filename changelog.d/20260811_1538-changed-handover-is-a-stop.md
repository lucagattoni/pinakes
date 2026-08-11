- **A boundary that needs a context clear is a stop, not an offer** (set by the user 20260811
  15:37). `CLAUDE.md`'s autonomous working mode said to *judge and say so* at each increment
  boundary, then carry on; it now says to finish the handoff, say so, and **stop** — since clearing
  is the user's command and no tool clears it, stopping is what makes the offer real. The handover
  itself is now a named step of the build procedure, [`docs/BUILDING.md` § *Hand over before you
  stop*](https://github.com/lucagattoni/pinakes/blob/main/docs/BUILDING.md): five places that go
  stale the moment an increment lands — `CLAUDE.md`'s live-plan pointer, `docs/README.md`'s
  plan-routing row, the plan's own increment mark, its baseline block, and `STATUS.md`'s surface
  row — all landed **in the same branch as the work**, and verified by opening what a fresh session
  opens rather than by trusting they were written somewhere.
