- **A release check that had never been made: does the published wheel contain the thing the release
  is named for?** `0.23.0`'s PyPI verification runs
  `uvx --no-cache --from "pinakes[light]==0.23.0" pnk ask --help` against the index as well as the
  usual `pnk --version`. A matching version string is evidence about *packaging*; it says nothing
  about whether the increment is inside the artifact. Recorded in
  [STATUS § Published on PyPI](https://github.com/lucagattoni/pinakes/blob/main/docs/STATUS.md#published-on-pypi)
  as the check every release adding a surface should make. `0.23.0` itself also resolved on the
  **first** install attempt, unlike the previous three.
