- **The warning that says your `.gitignore` names `.pinakes/` but git ignores it anyway now points
  at a command that prints something.** It suggested `git check-ignore -v .pinakes/index.db`, and
  that reports only *positively matched* paths — so in the one state the message is printed for, it
  produced empty output and exit 1. It now suggests `grep -n pinakes .gitignore`, which shows the
  line and the `!` re-include that defeats it, in your own file. Also in this fix: a
  `GIT_CEILING_DIRECTORIES` you set is honoured rather than stripped, so the check agrees with what
  your own `git add` would do from the same directory — unlike `GIT_DIR` and `GIT_WORK_TREE`, which
  redirect git at a *different* repository and are still stripped.
