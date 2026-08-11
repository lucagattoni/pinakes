- **`pnk init --backend st|light` stamps the matching embedding and rerank models in both blocks.**
  Every real KB stamped from `notes` immediately edited `provider` in *both* `[embedding]` and
  `[rerank]`, always for the same reason — a `[light]` install — and the GUIDE documented doing it
  by hand as the normal path. The default is unchanged: omit the flag and you get
  `sentence-transformers`, exactly as before.
- **It is a flag rather than detection, and the docs no longer claim otherwise.** Three places said
  `pnk init` "cannot see which extra you installed"; `importlib.util.find_spec` can, and `embed.py`
  already uses it. Stamping what it sees was rejected anyway: `pinakes.toml` is portable and
  committed, so writing a machine-local fact into it bakes one author's install into a file their
  collaborators read, and the KB then fails for whoever has the other extra. A flag records a
  choice; sniffing records an accident.
