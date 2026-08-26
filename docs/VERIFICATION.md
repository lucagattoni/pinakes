# Verification — every promise, and the test that holds it

`plans/20260727_1543-v0.2.md` ends with a table headed *"Every row carries an increment number and a test path — a
promise in a section with no owner is a wish"*. **Sixty-one of its ninety-eight test paths did not
resolve.** Not because the properties went untested — almost all of them are tested, usually under a
better name than the plan guessed — but because the plan wrote its test names *before* the tests
existed, and implementation renamed them. A verification table whose paths cannot be resolved
verifies nothing; it is the wish it warned about, wearing the table's clothes.

So the plan keeps its predictions, as the historical record of what was intended, and **this file is
the resolved mapping**: what must be true, and the test that actually holds it, in the tree as it
stands. [`tests/test_verification.py`](https://github.com/lucagattoni/pinakes/blob/main/tests/test_verification.py) asserts every test named below
exists — so this table can go stale exactly once, in the commit that breaks it, and not silently.

A row saying **none** is a promise with no test. There are none today; if you add a row, add its
test, or write **none** and say why in the same commit.

**Two limits, stated so nobody reads this as more than it is.**

* **The gate checks that each named test *exists*, not that it asserts the property beside it.** No
  test can check that. The mapping below was resolved by reading the tests where the name did not
  make it obvious — and the I9 review still found one row mapped from a name alone, which was
  wrong (the completeness audit's). Treat a row as a strong pointer, not a proof.
* **The scope began as `plans/20260727_1543-v0.2.md`'s promises**, which is what the table this
  replaces covered, and has grown with the work since. **Re-measured 20260825 18:38 UTC, on the tree this commit
  creates: 904 rows, 45 distinct increment ids** — **not enumerated here on purpose.** A range
  like *I1–I11* reads as a claim that every id in it has a row, and four do not (I10, T6, E2 and E6
  have none; T6 is the deferred `sqlite-vec` tier, so it *cannot*), while `L5b` is real and no range
  contains it. **Count them with the gate's filter rather than trusting a range**, **naming 63 of the 74 test modules in `tests/`.** The parent
  `03e6f86` measured 890 and 44; **this change is what moved them**, by adding the fourteen
  server-boundary rows below — stated because a count restated from the parent commit would have been
  falsified by the very edit that restated it. An earlier version of this paragraph said
  the table *"stopped"* at 0.12.0 and that the gap was *"four releases wide"*; both were true when
  written and neither has been true for a long time. **Do not restate a release count here** — it
  goes stale silently, which is what happened. State what was measured and when — **and count the rows
  the way the gate does**: an earlier version of this paragraph said 923, which counted the table
  headers `tests/test_verification.py` skips — 33 of them at the time, **35** now — the MCP section added one and the
  markdown-link table's missing header added another, which is the same moving-denominator trap one layer down. **The module figure had rotted the same way and worse**
  — it said *62 of the 67*, wrong on both halves; there are 74 modules and 63 carry a row. Count them
  with the gate's own `REFERENCE` regex, not by searching the file for a filename: the eleven unnamed
  module names are spelled out in the bullet directly below, so a substring test over this file scores
  them as covered and reports 74 of 74, finding nothing.
* **Two gaps remain, and they are different in kind.** **Six modules carry zero rows** —
  `test_chunk.py`, `test_ids.py`, `test_lock.py`, `test_pairing.py`, `test_uri.py`, `test_embed.py`.
  They predate the table and are not unowned. **Five more are named by no row at all** —
  `test_build_rfc_corpus.py`, `test_deep_reservation.py`, `test_measure_sync_cpu.py`,
  `test_rfc_golden_set.py`, `test_two_leg_gate.py`. **`test_init.py` is no longer among them: it
  carries 27 rows**, and `test_eval.py` carries 32 throughout *The golden set, per question (G2)* —
  both were once listed here as absent, in error, and each correction was found by counting rather
  than by reading.
* **D-34 is answered: this table maps *promises*, not every test.** Taken by the user
  **20260825 18:16 UTC** ([`plans/20260825_1803-open-decisions.md`](https://github.com/lucagattoni/pinakes/blob/main/plans/20260825_1803-open-decisions.md)),
  ratifying the reading `db7d1c1` had already operated on since 20260804. **A promise is a
  user-visible guarantee, a named invariant, or a gate's own correctness.** It is *not* a unit test
  of an internal primitive, and it is *not* a per-surface re-assertion of a promise already rowed
  elsewhere. `tests/` holds **2 051** test functions against these 904 rows, and **that ratio is not by
  itself evidence of a hole** — a sample of the residue found those two categories dominate it. That
  inference was drawn here once anyway, by a planner, hours after the lesson that named it.
* **But "not systematically debt" is not "no debt", and the difference was measured rather than
  argued.** The pass that took D-34 sampled the residue and found a genuine unrowed promise; **an
  audit of `tests/test_serve.py` then found it was not alone — 14 of that module's 31 tests carried
  no row, including the MCP server's path-refusal boundary and the labelling of retrieved text as
  evidence rather than instruction.** The cause was structural: the server's rows lived under
  *the links release* and *page citations*, and **no section owned the server boundary itself**. One
  now does, below. **Do not read this as a backlog to burn down** — the point is that the residue is
  mixed, so a promise-shaped test in it gets rowed when found, and a unit test does not.
* **What still has no gate is the direction.** `tests/test_verification.py` walks from this document
  to the tests, so it proves no row is fiction; it **cannot** prove no guarantee is unrowed, and
  D-34 deliberately did not buy that. The one-directionality is *"not a defect in the gate, it is the
  shape of the problem, so the answer is procedural"* (`db7d1c1`, 20260804) — recorded here because
  it was previously reachable only from a commit message, which is why every fresh reader who counted
  the tree re-derived the question.

## Packaging and the extractor registry

| What must be true | Increment | Where it is checked |
|---|---|---|
| no extractor library enters `[project.dependencies]` | I1 | `check.sh` gate + `tests/test_packaging.py::test_extractors_stay_extras` |
| `pinakes[claude]` cannot be installed without `[pdf]` | I1 | `tests/test_packaging.py::test_claude_extra_requires_pdf_extra` |
| Pillow stays dev-only — never core, never an extra | I2 | `tests/test_packaging.py::test_pillow_is_dev_only_never_core_and_never_an_extra` |
| the `mcp` requirement cannot admit a major without `mcp.server.mcpserver` | fix | `tests/test_packaging.py::test_the_mcp_requirement_excludes_every_major_without_mcpserver` |
| every module of an *installed* Pinakes imports against a fresh resolve | fix | CI `build` + `release.yml`, pinned by `tests/test_check_script.py::test_ci_imports_every_module_out_of_a_freshly_resolved_wheel_and_proves_it_can_fail` |
| …and the gate cannot report a pass it did not earn | fix | `tests/test_wheel_import_gate.py::test_an_allowance_covers_only_the_module_it_names_even_for_the_same_library` + `tests/test_wheel_import_gate.py::test_a_required_module_may_not_also_be_allowed_to_fail` + `tests/test_wheel_import_gate.py::test_a_package_outside_site_packages_is_refused` + `tests/test_wheel_import_gate.py::test_a_package_with_no_file_is_refused_rather_than_resolved_to_the_cwd` |
| a freshly-resolved install answers an MCP handshake, before publishing | fix | CI `build` + `release.yml`, pinned by `tests/test_check_script.py::test_ci_drives_a_real_mcp_handshake_against_a_freshly_resolved_install` + `tests/test_check_script.py::test_the_release_workflow_exercises_the_wheel_it_is_about_to_publish` |
| …and that handshake is watched failing for the reason it claims | fix | `tests/test_check_script.py::test_the_handshake_gate_is_watched_failing_for_the_reason_it_claims` |
| the four `pinakes_*` tool schemas a client is handed are the committed ones | fix | `tests/test_mcp_handshake_gate.py::test_a_real_session_lists_exactly_the_committed_tool_schemas` |
| a client is told **Pinakes'** version, never the `mcp` library's | fix | `tests/test_mcp_handshake_gate.py::test_the_version_a_client_is_told_is_pinakes_own_and_not_the_mcp_librarys` |
| …and the handshake gate cannot report a pass it did not earn | fix | `tests/test_mcp_handshake_gate.py::test_a_snapshot_that_does_not_match_fails_and_shows_which_line_moved` + `tests/test_mcp_handshake_gate.py::test_a_missing_snapshot_is_refused_before_a_server_is_ever_spawned` + `tests/test_mcp_handshake_gate.py::test_a_command_that_is_not_on_path_is_refused_rather_than_reported_as_a_pass` + `tests/test_mcp_handshake_gate.py::test_expect_version_is_required_unless_the_snapshot_is_being_updated` |
| a core-only install fails naming the extra | I1 | `tests/test_extract.py::test_a_missing_extra_names_the_install_command` |
| every backend's missing-extra error names its own extra | I1 | `tests/test_extract.py::test_backend_requirement_names_the_extra_a_user_is_told_to_install` |
| an unknown backend is rejected from the manifest | I1 | `tests/test_manifest.py::test_extraction_backend_must_be_registered` |
| …and from `--extract`, without importing anything | I1 | `tests/test_cli.py::test_unknown_extract_flag_is_rejected` |
| availability is answered without executing the backend | I1 | `tests/test_extract.py::test_is_backend_installed_locates_without_executing` |
| one unreadable PDF does not block the corpus | I1 | `tests/test_sync.py::test_a_pdf_fails_at_extraction_but_does_not_block_the_rest` |
| a sidecar that will not parse is never overwritten | fix | `tests/test_sync.py::test_an_unreadable_sidecar_is_never_overwritten` |
| ...and does not stop the other documents | fix | `tests/test_sync.py::test_an_unreadable_sidecar_does_not_stop_the_other_documents` |
| ...on the pre-commit path either | fix | `tests/test_sync.py::test_sidecars_only_refuses_the_unreadable_one_and_mints_the_rest` |
| ...and `--index-only` indexes no divergent id | fix | `tests/test_sync.py::test_index_only_neither_writes_nor_indexes_a_divergent_id` |
| minting refuses where a file already exists | fix | `tests/test_sidecar.py::test_create_refuses_to_overwrite_an_existing_sidecar` |
| ...while `write` still overwrites, for I5's merge | fix | `tests/test_sidecar.py::test_write_still_overwrites_because_a_merge_needs_it` |
| a broken sidecar on an indexed document does not abort the sync | fix | `tests/test_sync.py::test_breaking_a_sidecar_after_indexing_does_not_abort_the_whole_sync` |
| a rebuild does not overwrite one either | fix | `tests/test_sync.py::test_a_rebuild_does_not_overwrite_an_unreadable_sidecar` |
| the refusal names the parse error, not just the existence | fix | `tests/test_sync.py::test_the_refusal_names_the_parse_error_not_merely_the_existence` |
| a sidecar that arrives after the walk asks for a rerun | fix | `tests/test_sync.py::test_a_sidecar_that_appears_after_the_walk_asks_for_a_rerun` |
| a write failure is recorded, never raised, on the pre-commit path | fix | `tests/test_sync.py::test_a_write_failure_on_the_pre_commit_path_is_recorded_not_raised` |
| minting refuses a dangling symlink too | fix | `tests/test_sidecar.py::test_create_refuses_a_dangling_symlink_too` |

## The links release: the corpora, the density gate and reverse-scan (L1–L2)

Authored links are sparse by design, so the corpora are gated on it; and a reverse scan reads
someone else's KB, so every failure mode has to be named rather than swallowed.

| What must be true | Increment | Where it is checked |
|---|---|---|
| both committed corpora load and name each other by ULID | L1 | `tests/test_partner_kb.py::test_both_corpora_load_and_validate` |
| every sidecar ULID is well-formed and unique across both KBs | L1 | `tests/test_partner_kb.py::test_every_sidecar_ulid_is_wellformed_and_unique_across_both_kbs` |
| every authored link target is a resolvable URI | L1 | `tests/test_partner_kb.py::test_every_link_target_is_a_resolvable_uri` |
| authored links are sparse (the density cap) | L1 | `tests/test_partner_kb.py::test_a_corpus_over_the_density_cap_fails_the_gate` |
| ...and the cap's boundary passes from the other side | L1 | `tests/test_partner_kb.py::test_a_corpus_exactly_at_the_cap_passes` |
| no single hub document, whatever the density | L1 | `tests/test_partner_kb.py::test_a_corpus_with_a_hub_document_fails_the_gate` |
| a corpus linked only outward is refused | L1 | `tests/test_partner_kb.py::test_a_corpus_whose_links_are_all_cross_kb_fails_the_gate` |
| ...but a corpus with no links at all is not | L1 | `tests/test_partner_kb.py::test_a_corpus_with_no_links_at_all_passes` |
| the gate runs without an index, and builds none | L1 | `tests/test_partner_kb.py::test_the_gate_runs_without_an_index` |
| the gate's count is the population `pnk doctor` reports | L1 | `tests/test_partner_kb.py::test_the_committed_split_is_pinned` |
| the corpus carries L2's `self`-form fixture | L1 | `tests/test_partner_kb.py::test_the_partner_corpus_carries_a_self_form_link` |
| the corpus carries L7's dangling-target fixture | L1 | `tests/test_partner_kb.py::test_the_partner_corpus_carries_a_target_in_a_kb_nothing_provides` |
| a hub behind a shared filename still fails the gate | L1 | `tests/test_partner_kb.py::test_a_hub_hiding_behind_a_shared_filename_still_fails` |
| an orphaned sidecar does not dilute density | L1 | `tests/test_partner_kb.py::test_an_orphaned_sidecar_does_not_dilute_the_density` |
| a document with no sidecar is still counted | L1 | `tests/test_partner_kb.py::test_a_document_without_a_sidecar_is_still_counted` |
| both corpora parse through the product's own sidecar reader | L1 | `tests/test_partner_kb.py::test_both_corpora_survive_the_products_own_sidecar_reader` |
| the gate's link count agrees with the product's | L1 | `tests/test_partner_kb.py::test_the_gate_and_the_product_agree_on_the_link_count` |
| `check.sh` still invokes the link-density gate | L1 | `tests/test_check_script.py::test_check_sh_declares_the_link_density_gate` |
| CI runs it and proves it can fail | L1 | `tests/test_check_script.py::test_ci_runs_the_link_density_gate_and_proves_it_can_fail` |
| inbound rows carry the other KB's id as source | L2 | `tests/test_sync_links.py::test_inbound_rows_carry_the_other_kbs_id_as_source` |
| a partner's `self` link resolves to the partner, not to us | L2 | `tests/test_sync_links.py::test_a_self_link_in_a_partner_sidecar_resolves_to_the_partner_not_the_local_kb` |
| only links targeting this KB are recorded | L2 | `tests/test_sync_links.py::test_a_partner_link_to_a_third_kb_is_not_recorded` |
| `kb_refs` records alias, path and scan time | L2 | `tests/test_sync_links.py::test_kb_refs_records_alias_path_and_scan_time` |
| the scan reads sidecars, never the partner's index | L2 | `tests/test_sync_links.py::test_the_scan_reads_sidecars_not_the_partners_index` |
| a reverse row never overwrites an authored one | L2 | `tests/test_sync_links.py::test_a_reverse_row_never_overwrites_an_authored_row` |
| an authored row reclaims a tuple a reverse scan wrote | L2 | `tests/test_sync_links.py::test_an_authored_row_reclaims_a_tuple_a_reverse_scan_already_wrote` |
| reverse rows never enter the authored count | L2 | `tests/test_sync_links.py::test_reverse_rows_never_enter_the_authored_count` |
| a removed link removes its reverse row | L2 | `tests/test_sync_links.py::test_a_removed_link_removes_its_reverse_row` |
| the delete is scoped to the scanned KB | L2 | `tests/test_sync_links.py::test_the_delete_is_scoped_to_the_scanned_kb` |
| a delisted KB's rows and `kb_refs` entry go with it | L2 | `tests/test_sync_links.py::test_delisting_a_linked_kb_removes_its_reverse_rows_and_kb_ref` |
| a failed scan deletes nothing | L2 | `tests/test_sync_links.py::test_a_failed_scan_leaves_the_previous_reverse_rows_in_place` |
| ...and does not stamp `last_scan` | L2 | `tests/test_sync_links.py::test_a_failed_scan_does_not_stamp_last_scan` |
| a mismatched KB id writes nothing at all | L2 | `tests/test_sync_links.py::test_a_mismatched_kb_id_writes_nothing_at_all` |
| each failure mode is recorded with its reason | L2 | `tests/test_sync_links.py::test_each_failure_mode_is_recorded_with_its_reason` |
| an unreachable linked KB does not fail the sync | L2 | `tests/test_sync_links.py::test_an_unreachable_linked_kb_does_not_fail_the_sync` |
| a fresh `kb_refs` entry skips the walk | L2 | `tests/test_sync_links.py::test_a_fresh_kb_refs_entry_skips_the_walk` |
| an expired window forces a rescan | L2 | `tests/test_sync_links.py::test_an_expired_ttl_forces_a_rescan` |
| `--scan-links` forces a rescan | L2 | `tests/test_sync_links.py::test_scan_links_forces_a_rescan` |
| the window never reads uncertainty as fresh | L2 | `tests/test_sync_links.py::test_the_ttl_never_reads_uncertainty_as_fresh` |
| `--sidecars-only` does not scan | L2 | `tests/test_sync_links.py::test_sidecars_only_does_not_scan` |
| ...and refuses `--scan-links` | L2 | `tests/test_sync_links.py::test_sidecars_only_with_scan_links_is_refused` |
| a rebuild reconstructs reverse rows from sidecars alone | L2 | `tests/test_sync_links.py::test_rebuild_reconstructs_reverse_rows_from_sidecars_alone` |
| the partner is never locked, even mid-sync | L2 | `tests/test_sync_links.py::test_the_partner_is_never_locked` |
| a vanished partner root deletes nothing | L2 | `tests/test_sync_links.py::test_a_vanished_partner_root_deletes_nothing` |
| a partner's `exclude` is honoured | L2 | `tests/test_sync_links.py::test_a_partners_exclude_is_honoured` |
| a partner's bad `include` cannot crash the sync | L2 | `tests/test_sync_links.py::test_a_partners_bad_include_pattern_does_not_crash_the_sync` |
| a partner root outside its own KB is refused | L2 | `tests/test_sync_links.py::test_a_partner_root_outside_its_own_kb_is_refused` |
| a failed local run does not blame the partner | L2 | `tests/test_sync_links.py::test_a_failed_local_run_does_not_blame_the_partner` |

## The links release: traversal, `pnk links` and `pinakes_links` (L3–L5)

Depth in **logical hops**, the double cap, `frontier` and `unresolved` — the properties a
caller cannot check for itself, on both the CLI and the MCP surface.

| What must be true | Increment | Where it is checked |
|---|---|---|
| depth counts one hop per candidate | L3 | `tests/test_traverse.py::test_depth_counts_one_hop_per_candidate` |
| depth is clamped server-side | L3 | `tests/test_traverse.py::test_depth_is_clamped_to_the_server_maximum` |
| fan-out keeps the highest-ranked, not the first k | L3 | `tests/test_traverse.py::test_fanout_keeps_the_highest_ranked_neighbours_not_the_first_k` |
| fan-out is clamped server-side | L3 | `tests/test_traverse.py::test_fanout_is_clamped_to_the_server_maximum` |
| ranking without a query uses edge weight | L3 | `tests/test_traverse.py::test_ranking_without_a_query_uses_edge_weight_then_distance` |
| ranking with a query uses provider similarity | L3 | `tests/test_traverse.py::test_ranking_with_a_query_uses_provider_supplied_similarity` |
| a capped answer is reproducible | L3 | `tests/test_traverse.py::test_ranking_is_totally_ordered_so_a_capped_answer_is_reproducible` |
| the frontier carries why each neighbour was not expanded | L3 | `tests/test_traverse.py::test_a_frontier_entry_carries_the_reason_it_was_not_expanded` |
| terminal outranks fanout when both apply | L3 | `tests/test_traverse.py::test_terminal_outranks_fanout_when_both_apply` |
| a cross-KB neighbour is terminal at every depth | L3 | `tests/test_traverse.py::test_a_cross_kb_neighbour_is_frontier_terminal_at_every_depth` |
| ...and is never asked for its own neighbours | L3 | `tests/test_traverse.py::test_a_terminal_neighbour_is_never_asked_for_its_own_neighbours` |
| a hub is expanded once globally | L3 | `tests/test_traverse.py::test_a_hub_is_expanded_once_globally` |
| a cycle terminates | L3 | `tests/test_traverse.py::test_a_cycle_terminates` |
| the token budget is independent of the row cap | L3 | `tests/test_traverse.py::test_the_token_budget_sets_truncated_independently_of_the_row_cap` |
| an answer within both caps reports neither | L3 | `tests/test_traverse.py::test_an_answer_within_both_caps_reports_neither` |
| unresolved targets survive to the caller | L3 | `tests/test_traverse.py::test_unresolved_targets_survive_to_the_caller` |
| `check.sh` still invokes the traversal-cap gate | L3 | `tests/test_check_script.py::test_check_sh_declares_the_traversal_cap_gate` |
| CI runs it too | L3 | `tests/test_check_script.py::test_ci_runs_the_traversal_cap_gate` |
| every neighbour is a document | L4 | `tests/test_cli_links.py::test_every_neighbour_is_a_document` |
| a cross-KB neighbour is terminal | L4 | `tests/test_cli_links.py::test_a_cross_kb_neighbour_is_marked_terminal` |
| ...carries its KB ULID and no title | L4 | `tests/test_cli_links.py::test_a_cross_kb_neighbour_carries_its_kb_ulid_and_no_title` |
| a same-KB neighbour carries its title | L4 | `tests/test_cli_links.py::test_a_same_kb_neighbour_carries_its_title` |
| `kb_id` is a ULID, never a name | L4 | `tests/test_cli_links.py::test_kb_id_is_a_ulid_not_a_name` |
| the JSON shape is pinned | L4 | `tests/test_cli_links.py::test_json_output_shape_is_pinned` |
| depth beyond the cap is served at the cap | L4 | `tests/test_cli_links.py::test_depth_beyond_the_cap_is_served_at_the_cap` |
| ...and depth is honoured, not merely capped | L4 | `tests/test_cli_links.py::test_depth_is_honoured_not_merely_capped` |
| one query per hop, never a recursive CTE | L4 | `tests/test_cli_links.py::test_one_query_per_hop_not_a_recursive_cte` |
| a missing local target is unresolved, never a neighbour | L4 | `tests/test_cli_links.py::test_a_local_link_to_a_missing_document_is_unresolved_not_dropped` |
| a cross-KB target is never called unresolved | L4 | `tests/test_cli_links.py::test_a_cross_kb_target_is_never_called_unresolved` |
| the frontier is capped like the rest of the response | L3 | `tests/test_traverse.py::test_the_frontier_is_capped_like_the_rest_of_the_response` |
| a frontier entry is retracted when the node is reached later | L3 | `tests/test_traverse.py::test_a_frontier_entry_is_retracted_when_the_node_is_reached_later` |
| ...but `terminal` and `depth` describe accepted nodes and stay | L3 | `tests/test_traverse.py::test_an_accepted_node_may_still_be_on_the_frontier_for_terminal_or_depth` |
| the response caps are clamped server-side too | L3 | `tests/test_traverse.py::test_the_response_caps_are_clamped_server_side_too` |
| terminal outranks the response caps, not only fanout | L3 | `tests/test_traverse.py::test_terminal_outranks_the_response_caps_as_well_as_fanout` |
| two relations to one target are two rows | L3 | `tests/test_traverse.py::test_two_relations_to_one_target_are_two_rows` |
| ...while the node is still expanded once | L3 | `tests/test_traverse.py::test_a_node_reachable_two_ways_is_still_expanded_once` |
| the row cap keeps the highest-ranked across the whole hop | L3 | `tests/test_traverse.py::test_the_row_cap_keeps_the_highest_ranked_across_the_whole_hop` |
| a score says whether it came from the query | L3 | `tests/test_traverse.py::test_a_score_says_whether_it_came_from_the_query` |
| `adjacent_k` defaults to 8 | L3 | `tests/test_manifest.py::test_adjacent_k_defaults_to_eight` |
| ...and above the cap is refused, not clamped | L3 | `tests/test_manifest.py::test_adjacent_k_above_the_server_cap_is_refused_not_clamped` |
| `pinakes_links` returns `score` and `frontier` on every return | L5 | `tests/test_serve.py::test_pinakes_links_returns_score_and_frontier_on_every_return` |
| ...and `confidence: unknown` with a query and without | L5 | `tests/test_serve.py::test_pinakes_links_reports_unknown_confidence_with_and_without_a_query` |
| a neighbour outside the served KBs carries its `kb_id` and a reason | L5 | `tests/test_serve.py::test_a_neighbour_outside_the_served_kbs_returns_its_kb_id_and_a_reason` |
| a neighbour it returns is fetchable by `pinakes_get` | L5 | `tests/test_serve.py::test_pinakes_get_resolves_a_neighbour_returned_by_pinakes_links` |
| depth is capped at the documented 3 over MCP too | L5 | `tests/test_serve.py::test_depth_is_capped_server_side` |
| a cross-KB neighbour is terminal over MCP too | L5 | `tests/test_serve.py::test_a_cross_kb_neighbour_is_terminal_over_mcp_too` |
| an unknown document is refused with a remedy | L5 | `tests/test_serve.py::test_an_unknown_document_is_refused_with_a_remedy` |
| the `pinakes_search` and `pinakes_get` payloads are unchanged | L5 | `tests/test_serve.py::test_pinakes_search_and_get_payloads_are_unchanged` |
| the tool is namespaced alongside the other three | L5 | `tests/test_serve.py::test_the_tools_are_namespaced` |
| the free-path gate **invokes** it, never only lists it | L5 | `tests/test_paid_path.py::test_the_free_path_never_imports_the_paid_client` (through `tests/free_path_run.py`) |
| `direction` is per relation, not per node | L5 | `tests/test_graph_present.py::test_direction_is_per_relation_not_per_node` |
| ...and one relation written from both ends is `both` | L5 | `tests/test_graph_present.py::test_one_relation_written_from_both_ends_is_both` |
| an unknown `direction` is refused, not answered emptily | L5 | `tests/test_graph_present.py::test_an_unknown_direction_is_refused_rather_than_answered_emptily` |
| `scored_by_query` says which scale `score` is on | L5 | `tests/test_graph_present.py::test_scored_by_query_says_which_scale_the_score_is_on` |
| a score is rounded to four places | L5 | `tests/test_graph_present.py::test_a_score_is_rounded_even_when_the_raw_value_is_long` |
| ...over a real KB too | L5 | `tests/test_graph_present.py::test_a_score_is_rounded_to_four_places` |
| `truncated` reports the caps that bit | L5 | `tests/test_graph_present.py::test_truncated_reports_the_caps_that_bit` |
| a frontier entry carries the distance it was found at | L5 | `tests/test_graph_present.py::test_a_frontier_entry_carries_the_distance_it_was_found_at` |
| every direction has its own arrow, the unreachable one included | L5 | `tests/test_graph_present.py::test_every_direction_has_its_own_arrow_including_the_one_no_fixture_can_reach` |
| the CLI says *why* a walk returned nothing | L5 | `tests/test_cli_links.py::test_the_cli_says_so_when_every_link_dangles` |
| ...filter before dangling, with both true at once (CLI) | L5 | `tests/test_cli_links.py::test_a_filtered_walk_reports_the_filter_before_the_dangling_links` |
| ...and over MCP | L5 | `tests/test_serve.py::test_a_filtered_walk_reports_the_filter_before_the_dangling_links` |
| a query reaches the ranking on both surfaces | L5 | `tests/test_graph_present.py::test_a_query_reaches_the_ranking_on_both_surfaces` |
| a document whose links all dangle is not called unlinked | L5 | `tests/test_serve.py::test_a_document_whose_links_all_dangle_is_not_called_unlinked` |
| a direction does not change with `depth` | L5 | `tests/test_graph_present.py::test_a_direction_does_not_change_with_depth` |
| `present`'s key constants match the rows | L5 | `tests/test_graph_present.py::test_the_projections_key_sets_match_what_the_rows_carry` |
| every argument that can empty an answer is named | L5 | `tests/test_graph_present.py::test_is_filtered_names_every_argument_that_can_empty_an_answer` |
| each direction gets its own arrow in the human output | L5 | `tests/test_cli_links.py::test_the_human_output_names_each_direction_with_its_own_arrow` |
| a local neighbour carries a title, a cross-KB one does not | L5 | `tests/test_graph_present.py::test_a_local_neighbour_carries_a_title_and_a_cross_kb_one_does_not` |
| an unresolved row survives and carries the local `kb_id` | L5 | `tests/test_graph_present.py::test_an_unresolved_row_survives_and_carries_the_local_kb_id` |
| every row shape is pinned by literal | L5 | `tests/test_graph_present.py::test_every_row_shape_is_pinned_by_literal` |
| the CLI and MCP surfaces project the same keys | L5 | `tests/test_graph_present.py::test_the_two_surfaces_project_the_same_keys` |
| an empty answer says whether the arguments emptied it | L5 | `tests/test_serve.py::test_an_empty_answer_says_whether_the_arguments_emptied_it` |
| a neighbour in a second served KB says which KB to fetch it from | L5 | `tests/test_serve.py::test_a_neighbour_in_a_second_served_kb_says_which_kb_to_fetch_it_from` |
| an alias is resolved to a ULID before it reaches disk | L6 | `tests/test_cli_link.py::test_an_alias_is_resolved_to_a_ulid_on_write` |
| ...and so is `self` | L6 | `tests/test_cli_link.py::test_self_is_expanded_on_write` |
| all three target grammars resolve | L6 | `tests/test_cli_link.py::test_each_dst_grammar_resolves` |
| ...with `pnk://` tried before the alias form | L6 | `tests/test_cli_link.py::test_a_pnk_uri_wins_over_an_alias_that_happens_to_be_called_pnk` |
| ...and a colon in a path is still a path | L6 | `tests/test_cli_link.py::test_a_colon_in_a_path_that_is_not_a_declared_alias_stays_a_path` |
| a well-formed `pnk://` to an absent target is written | L6 | `tests/test_cli_link.py::test_a_well_formed_pnk_uri_to_an_absent_target_is_written` |
| an unresolvable target is refused with its remedy | L6 | `tests/test_cli_link.py::test_an_unresolvable_dst_is_refused_with_its_remedy` |
| ...including an alias whose KB is not on this machine | L6 | `tests/test_cli_link.py::test_an_alias_pointing_at_a_kb_that_is_not_here_is_refused` |
| ...and one whose partner declares a different `[kb] id` | L6 | `tests/test_cli_link.py::test_an_alias_whose_partner_declares_a_different_id_is_refused` |
| a source with no sidecar is refused, and none is minted | L6 | `tests/test_cli_link.py::test_a_source_with_no_sidecar_is_refused_and_none_is_minted` |
| an unreadable source sidecar is never overwritten | L6 | `tests/test_cli_link.py::test_an_unreadable_source_sidecar_is_never_overwritten` |
| a source outside the KB is refused | L6 | `tests/test_cli_link.py::test_a_source_outside_the_kb_is_refused` |
| ...and a sidecar named as the source | L6 | `tests/test_cli_link.py::test_a_sidecar_named_as_the_source_is_refused` |
| an empty `--rel` is refused before anything is read | L6 | `tests/test_cli_link.py::test_an_empty_rel_is_refused_before_anything_is_read` |
| ...and a missing one is a usage error | L6 | `tests/test_cli_link.py::test_a_missing_rel_is_a_usage_error` |
| comments survive a rewrite through `pnk link` | L6 | `tests/test_cli_link.py::test_comments_survive_a_rewrite_through_pnk_link` |
| unknown keys inside a link entry survive it | L6 | `tests/test_cli_link.py::test_unknown_keys_inside_a_link_entry_survive_through_pnk_link` |
| no line outside the `links` block changes | L6 | `tests/test_cli_link.py::test_no_line_outside_the_links_block_changes_when_a_link_is_added` |
| ...while an indented block is reindented (pinned) | L6 | `tests/test_cli_link.py::test_an_indented_links_block_is_reindented_when_a_link_is_added` |
| ...and a document-trailing comment is captured (pinned) | L6 | `tests/test_cli_link.py::test_a_document_trailing_comment_is_captured_when_the_first_link_is_appended` |
| a first link into a null `links` value does not crash | L6 | `tests/test_cli_link.py::test_a_first_link_into_a_null_links_value_does_not_crash` |
| a `rel` that looks like a boolean is quoted, on both write paths | L6 | `tests/test_cli_link.py::test_a_rel_that_looks_like_a_boolean_is_quoted`, `::test_a_rel_that_looks_like_a_boolean_is_quoted_on_a_first_link_too` |
| the source document is byte-identical afterwards | L6 | `tests/test_cli_link.py::test_the_source_document_is_byte_identical_afterwards` |
| the write is atomic under an interrupted rename | L6 | `tests/test_cli_link.py::test_the_write_is_atomic_under_an_interrupted_rename` |
| the same link twice writes nothing the second time | L6 | `tests/test_cli_link.py::test_the_same_link_twice_writes_nothing_the_second_time` |
| ...while a second relation to one target is a second entry | L6 | `tests/test_cli_link.py::test_a_second_relation_to_the_same_target_is_a_second_entry` |
| what `pnk link` writes reaches the `links` table | L6 | `tests/test_cli_link.py::test_a_link_round_trips_through_sync_into_the_links_table` |
| the grammar is reachable without the CLI | L6 | `tests/test_cli_link.py::test_resolve_target_is_reachable_without_the_cli` |
| a document cannot link to itself | L6 review | `tests/test_cli_link.py::test_a_document_cannot_link_to_itself` |
| a symlinked document inside the KB can be linked | L6 review | `tests/test_cli_link.py::test_a_symlinked_document_inside_the_kb_can_be_linked` |
| ...while `..` is still refused | L6 review | `tests/test_cli_link.py::test_a_dot_dot_escape_is_still_refused` |
| ...and a symlinked *directory* cannot carry a link out of the KB | L6 review 2 | `tests/test_cli_link.py::test_a_symlinked_directory_cannot_carry_a_link_out_of_the_kb` |
| an absolute source behind a symlinked ancestor is accepted | L6 review 2 | `tests/test_cli_link.py::test_an_absolute_source_behind_a_symlinked_ancestor_is_accepted` |
| an unreadable or over-long path is refused, not a traceback | L6 review 3 | `tests/test_cli_link.py::test_an_unreadable_directory_is_refused_rather_than_crashing` |
| ...and an unreadable *partner* KB likewise | L6 review 4 | `tests/test_cli_link.py::test_a_partner_kb_that_cannot_be_read_is_unreachable_not_a_traceback` |
| ...and a `[[links.kb]] path` that will not expand | L6 review 5 | `tests/test_cli_link.py::test_a_linked_kb_path_that_will_not_expand_is_unreachable_not_a_traceback` |
| ...and the same class inside `linkscan`, on a git hook | L6 review 5 | `tests/test_sync_links.py::test_a_linked_kb_that_raises_before_the_handling_is_still_only_an_issue` |
| a partner with a malformed `[kb] id` names the KB it came from | L6 review 5 | `tests/test_cli_link.py::test_a_partner_with_a_malformed_kb_id_names_the_kb_it_came_from` |
| a `[[links.kb]] path` naming a regular file says so | L6 review 5 | `tests/test_cli_link.py::test_a_linked_kb_path_naming_a_regular_file_says_so` |
| ...and a `pinakes.toml` that is a directory or a broken symlink says which | L6 review 9 | `tests/test_cli_link.py::test_a_pinakes_toml_that_is_not_a_regular_file_says_which` |
| a partner `include` pattern reaching outside its KB is refused | L6 review 10 | `tests/test_sync_links.py::test_a_partner_include_pattern_outside_its_own_kb_is_refused` |
| ...while a symlinked document *inside* a partner KB is still read | L6 review 10 | `tests/test_sync_links.py::test_a_symlinked_document_inside_a_partner_kb_is_still_read` |
| ...refused **before** the glob, so the walk is bounded | L6 review 11 | `tests/test_sync_links.py::test_an_escaping_include_pattern_is_refused_without_walking` |
| ...while a `..` that stays *inside* the KB is not refused | L6 review 12 | `tests/test_sync_links.py::test_a_dot_dot_pattern_that_stays_inside_the_kb_is_not_refused` |
| ...and a symlinked escape stops at the first match | L6 review 12 | `tests/test_sync_links.py::test_a_symlinked_escape_stops_at_the_first_match` |
| ...and a *leading* glob does not defeat the refusal | L6 review 13 | `tests/test_sync_links.py::test_a_leading_glob_does_not_defeat_the_static_refusal` |
| a fixed and a glob include naming one symlinked document agree | L6 review 13 | `tests/test_sync_links.py::test_a_fixed_include_naming_a_symlinked_document_agrees_with_the_glob_spelling` |
| an absolute include says it is absolute, not that it escapes | L6 review 13 | `tests/test_sync_links.py::test_an_absolute_include_says_it_is_absolute_not_that_it_escapes` |
| ...and `**` before a `..` does not defeat the refusal | L6 review 14 | `tests/test_sync_links.py::test_a_double_star_before_a_dot_dot_does_not_defeat_the_refusal` |
| one unusable include pattern does not discard the others | L6 review 14 | `tests/test_sync_links.py::test_one_unusable_include_pattern_does_not_discard_the_others` |
| the walk raising is an issue, never a traceback | L6 review 14 | `tests/test_sync_links.py::test_the_walk_raising_is_an_issue_not_a_traceback` |
| ...for a bad `include` **or** `exclude` entry, without discarding the rest | L6 review 15 | `tests/test_sync_links.py::test_one_bad_sources_entry_is_one_problem_not_the_end_of_the_partner` |
| a trailing `..` in an include is refused | L6 review 15 | `tests/test_sync_links.py::test_a_trailing_dot_dot_include_is_refused` |
| only `**` is dropped from the containment probe | L6 review 15 | `tests/test_sync_links.py::test_only_double_star_is_dropped_from_the_probe` |
| a partner document with no sidecar contributes nothing | L6 review 15 | `tests/test_sync_links.py::test_a_partner_document_without_a_sidecar_contributes_nothing` |
| a pattern escaping under one root collects under none | L6 review 16 | `tests/test_sync_links.py::test_a_pattern_that_escapes_under_one_root_collects_under_none` |
| ...and an escape matching only sidecars is still reported | L6 review 11 | `tests/test_sync_links.py::test_an_escape_matching_only_sidecars_is_still_reported` |
| one escaping pattern is one problem, however many roots | L6 review 11 | `tests/test_sync_links.py::test_one_escaping_pattern_is_one_problem_however_many_roots` |
| `exclude` matches the path the partner wrote, not the resolved one | L6 review 11 | `tests/test_sync_links.py::test_an_exclude_rule_matches_the_path_the_partner_wrote_not_the_resolved_one` |
| the boundary is the KB root, not `[sources]` (stated residual) | L6 review 3 | `tests/test_cli_link.py::test_a_document_inside_the_root_but_outside_sources_can_be_linked` |
| a `~` path is refused, not a `RuntimeError` traceback | L6 review | `tests/test_cli_link.py::test_a_home_relative_path_is_refused_rather_than_crashing` |
| an empty `tags:`/`provenance:` is not normalised by a link | L6 review | `tests/test_cli_link.py::test_an_empty_tags_or_provenance_is_not_normalised_by_adding_a_link` |
| a symlinked sidecar is written through, not replaced | L6 review | `tests/test_cli_link.py::test_a_symlinked_sidecar_is_written_through_not_replaced` |
| `<alias>:` naming no document says so | L6 review | `tests/test_cli_link.py::test_an_alias_naming_no_document_says_so` |
| ...and a manifest declaring no linked KBs says that | L6 review | `tests/test_cli_link.py::test_a_kb_declaring_no_linked_kbs_says_that_rather_than_listing_none` |
| `resolve_path` never raises, and answers an **absolute** path or `None` | L6 review 7, 8 | `tests/test_sync_links.py::test_resolve_path_never_raises_whatever_the_manifest_says` |
| ...so an unresolvable path is reported, never silently fresh-skipped | L6 review 7, 8 | `tests/test_sync_links.py::test_an_unresolvable_path_is_reported_rather_than_fresh_skipped` |
| ...and an unresolvable path is never walked from the working directory | L6 review 8 | `tests/test_sync_links.py::test_an_unresolvable_path_is_never_walked_from_the_working_directory` |
| ...nor resolved through it into a permanent link | L6 review 8 | `tests/test_cli_link.py::test_an_unresolvable_linked_kb_path_is_never_resolved_through_the_working_directory` |
| an embedded NUL in a path is refused, not a `ValueError` traceback | L6 review 7 | `tests/test_cli_link.py::test_a_path_with_an_embedded_nul_is_refused_rather_than_crashing` |

## The MCP server boundary (I13)

`pnk serve` is the surface where the reader is an **LLM reading text it did not write**, and where
every argument arrives from outside. Its rows lived under *the links release* and *page citations*
until 20260825, so the boundary itself — what a tool argument may be, and what the payload says
about the text it carries — was held by tests that **no section owned**. Found by the bounded audit
D-34 licensed, not by a failure. Two of these are security boundaries and are marked as such.

| What must be true | Increment | Where it is checked |
|---|---|---|
| **a tool argument is never a path.** `pinakes_get` refuses `../../etc/passwd`, a repo-relative path, and a well-formed but unknown ULID alike, each with a remedy naming `pinakes_search` | I13 | `tests/test_serve.py::test_get_refuses_anything_that_is_not_a_known_id` |
| **retrieved text is labelled evidence, never instruction**, on the search payload *and* the get payload — the caller is an LLM reading text it did not write (DESIGN §4.7) | I13 | `tests/test_serve.py::test_retrieved_text_is_labelled_as_evidence_not_instruction` |
| only the KBs `pnk serve` was given are reachable; an unserved KB is refused, and the remedy says a KB is named and never addressed by path | I13 | `tests/test_serve.py::test_only_configured_kbs_are_reachable` |
| two served KBs sharing a name are refused **at startup**, rather than one silently shadowing the other | I13 | `tests/test_serve.py::test_two_kbs_with_the_same_name_are_refused_at_startup` |
| serving no KB at all is refused, with a remedy naming `pnk serve` | I13 | `tests/test_serve.py::test_serving_nothing_is_refused` |
| a document deleted since the server started is no longer fetchable | I13 | `tests/test_serve.py::test_a_deleted_document_cannot_be_fetched` |
| an index rebuilt underneath a running server is picked up — a replaced inode must not leave an open handle answering from the old one (DESIGN §6.5) | I13 | `tests/test_serve.py::test_an_index_swapped_underneath_is_picked_up` |
| a search answer carries a citation and a suggested next step | I13 | `tests/test_serve.py::test_search_returns_cited_evidence_and_a_next_step` |
| a ULID resolves through the index to its document | I13 | `tests/test_serve.py::test_get_resolves_a_ulid_through_the_index` |
| a KB is selectable by name or by ULID, and the first configured KB is the default | I13 | `tests/test_serve.py::test_a_kb_can_be_selected_by_name_or_ulid` |
| `pinakes_list_kbs` reports each KB's name, id and document count | I13 | `tests/test_serve.py::test_list_kbs_reports_document_counts` |

## The sidecar round-trip (L5b)

| What must be true | Increment | Where it is checked |
|---|---|---|
| an unknown key round-trips byte-identically | L5b | `tests/test_sidecar.py::test_an_unknown_key_round_trips_byte_identically` |
| comments survive a rewrite | L5b | `tests/test_sidecar.py::test_comments_survive_a_rewrite` |
| ...inside `provenance.extraction` | L5b | `tests/test_sidecar.py::test_a_comment_inside_provenance_extraction_survives_a_re_extraction` |
| ...on a `tags` entry | L5b | `tests/test_sidecar.py::test_a_comment_on_a_tags_entry_survives_a_rewrite` |
| ...and through both provenance helpers | L5b | `tests/test_sidecar.py::test_with_extraction_provenance_preserves_comments`, `::test_without_extraction_provenance_preserves_comments` |
| quoting style survives | L5b | `tests/test_sidecar.py::test_quoting_style_survives_a_rewrite` |
| block scalars and blank lines survive | L5b | `tests/test_sidecar.py::test_block_scalars_and_blank_lines_survive_a_rewrite` |
| a long spaced value is not folded | L5b | `tests/test_sidecar.py::test_a_value_with_spaces_past_eighty_columns_is_not_folded` |
| YAML 1.1 scalars are no longer corrupted | L5b | `tests/test_sidecar.py::test_yaml_1_1_scalars_are_no_longer_corrupted` |
| the user's key order is preserved | L5b | `tests/test_sidecar.py::test_the_users_key_order_is_preserved_on_rewrite` |
| ...while a minted sidecar is canonical | L5b | `tests/test_sidecar.py::test_a_minted_sidecar_still_uses_canonical_order` |
| `provenance` first appearing is appended, moving no comment | L5b | `tests/test_sidecar.py::test_provenance_first_appearing_is_appended_and_moves_no_comment` |
| links reconcile by `to`, not by position | L5b | `tests/test_sidecar.py::test_reordering_links_does_not_move_their_comments` |
| ...and a removed link takes only its own comment | L5b | `tests/test_sidecar.py::test_a_removed_link_takes_only_its_own_comment` |
| unknown per-link keys survive | L5b | `tests/test_sidecar.py::test_unknown_keys_inside_a_link_entry_survive_a_rewrite` |
| changed tags keep the surviving entries' comments | L5b | `tests/test_sidecar.py::test_changed_tags_keep_the_comments_of_the_entries_that_remain` |
| an unchanged known key is not reassigned | L5b | `tests/test_sidecar.py::test_an_unchanged_known_key_is_not_reassigned`, `::test_an_unchanged_links_block_is_not_rewritten` |
| a minted ambiguous title is quoted, read back through PyYAML | L5b | `tests/test_sidecar.py::test_a_minted_title_that_looks_like_a_boolean_is_quoted` |
| a duplicate key is refused without ruamel's suppression URL | L5b | `tests/test_sidecar.py::test_a_duplicate_key_is_refused_without_ruamels_suppression_url` |
| a JSON-unencodable value is refused with a remedy | L5b | `tests/test_sidecar.py::test_a_json_unencodable_extra_value_is_refused_with_a_remedy` |
| ...including `!!str` | L5b | `tests/test_sidecar.py::test_a_double_bang_str_value_is_refused` |
| ...while the tags that worked before still work | L5b | `tests/test_sidecar.py::test_the_standard_tags_that_worked_before_the_swap_still_work` |
| a custom-tagged mapping is accepted (documented widening) | L5b | `tests/test_sidecar.py::test_a_tagged_mapping_is_accepted_because_it_serialises` |
| a uniformly non-string-keyed mapping is a stated residual | L5b | `tests/test_sidecar.py::test_a_uniformly_non_string_keyed_mapping_is_a_stated_residual` |
| an explicit `!!` tag is stripped | L5b | `tests/test_sidecar.py::test_an_explicit_double_bang_tag_is_stripped` |
| an anchor on an empty value is destroyed | L5b | `tests/test_sidecar.py::test_an_anchor_on_an_empty_value_is_destroyed` |
| ...while one on a real value survives | L5b | `tests/test_sidecar.py::test_an_anchor_on_a_real_value_survives` |
| CRLF, BOM and `---`/`...` are not carried | L5b | `tests/test_sidecar.py::test_what_yaml_does_not_carry_is_not_carried` |
| a missing trailing newline is added | L5b | `tests/test_sidecar.py::test_a_missing_trailing_newline_is_added` |
| the AST scan catches a function-scoped import | L5b | `tests/test_packaging.py::test_the_ast_scan_catches_a_function_scoped_import` |
| the stub signature test catches a fabricated parameter | L5b | `tests/test_packaging.py::test_the_stub_signature_test_catches_a_fabricated_parameter` |
| ruamel's sequence reindentation is a documented exclusion | L5b | `tests/test_sidecar.py::test_a_two_space_indented_sequence_is_reindented` |
| two links sharing a `to` keep their own `rel` and comment | L5b | `tests/test_sidecar.py::test_two_links_sharing_a_to_keep_their_own_rel_and_comment` |
| a user key inside `provenance.extraction` survives a re-extraction | L5b | `tests/test_sidecar.py::test_a_user_key_inside_provenance_extraction_survives_a_re_extraction` |
| a document-trailing comment is captured by an appended key (pinned) | L5b | `tests/test_sidecar.py::test_a_document_trailing_comment_is_captured_by_an_appended_key` |
| reading a `%YAML` directive does not contaminate the next document | L5b | `tests/test_sidecar.py::test_reading_a_directive_does_not_contaminate_the_next_document` |
| ...nor a freshly minted sidecar | L5b | `tests/test_sidecar.py::test_a_minted_sidecar_is_not_contaminated_either` |
| a known key with a null value does not crash the writer | L5b | `tests/test_sidecar.py::test_a_known_key_with_a_null_value_does_not_crash_the_writer` |
| editing one `rel` where two links share a `to` moves neither comment | L5b | `tests/test_sidecar.py::test_editing_one_rel_where_two_links_share_a_to_moves_neither_comment` |
| a key that is not a string is reported as a key | L5b | `tests/test_sidecar.py::test_a_key_that_is_not_a_string_is_refused_as_a_key` |
| a reused anchor name is refused, not silently resolved | L5b | `tests/test_sidecar.py::test_a_reused_anchor_name_is_refused_rather_than_silently_resolved` |
| ...whatever the caller's warning filter says | L5b | `tests/test_sidecar.py::test_a_reused_anchor_is_refused_whatever_the_ambient_warning_filter_says` |
| a non-string key at the top level is refused | L5b | `tests/test_sidecar.py::test_a_non_string_key_at_the_top_level_is_refused` |
| two identical link entries both survive | L5b | `tests/test_sidecar.py::test_two_identical_link_entries_both_survive` |
| editing a `rel` updates the entry rather than replacing it | L5b | `tests/test_sidecar.py::test_editing_a_rel_updates_the_entry_rather_than_replacing_it` |
| **every committed sidecar round-trips** (the exit criterion) | L5b | `tests/test_partner_kb.py::test_every_committed_sidecar_round_trips_through_read_and_write` |
| a `self` link keeps its place, comment and unknown keys | L5b | `tests/test_sidecar.py::test_a_self_link_keeps_its_place_its_comment_and_its_unknown_keys` |
| a string field 1.2 resolves as a number is refused | L5b | `tests/test_sidecar.py::test_a_string_field_that_yaml_1_2_resolves_as_a_number_is_refused` |
| a tagged scalar in a known field is refused, without a ruamel class name | L5b | `tests/test_sidecar.py::test_a_tagged_scalar_in_a_known_field_is_refused_with_a_remedy` |
| a `rel` or tag that looks like a boolean is quoted when written | L5b | `tests/test_sidecar.py::test_a_rel_or_tag_that_looks_like_a_boolean_is_quoted_when_written` |
| ...including when the key first appears | L5b | `tests/test_sidecar.py::test_a_link_written_where_none_existed_is_quoted_too` |
| the two-resolver union covers PyYAML 1.1 | L5b | `tests/test_packaging.py::test_the_two_resolver_union_covers_pyyaml_1_1` |
| a self-referential anchor is nulled rather than refused (pinned) | L5b | `tests/test_sidecar.py::test_a_self_referential_anchor_is_nulled_rather_than_refused` |
| the deletion limitation is pinned, not fixed | L5b | `tests/test_sidecar.py::test_deleting_a_commented_key_loses_one_comment_and_misattributes_another` |
| `original` is excluded from equality | L5b | `tests/test_sidecar.py::test_the_original_document_is_excluded_from_equality` |
| an anchored or aliased boolean indexes as `true`, at every depth | L5b | `tests/test_sync.py::test_an_anchored_boolean_is_indexed_as_true_not_one` |
| `ruamel.yaml` is a core dependency | L5b | `tests/test_packaging.py::test_ruamel_yaml_is_a_core_dependency` |
| `pyyaml` is dev-only, never core, never an extra | L5b | `tests/test_packaging.py::test_pyyaml_is_dev_only_never_core_and_never_an_extra` |
| no module under `src/` imports PyYAML (AST) | L5b | `tests/test_packaging.py::test_no_module_under_src_imports_pyyaml` |
| ...nor does the free path load it (runtime) | L5b | `tests/test_paid_path.py::test_the_free_path_run_never_loads_yaml` |
| every stub symbol matches its real signature | L5b | `tests/test_packaging.py::test_every_symbol_the_ruamel_stub_declares_matches_inspect_signature` |

## The PDF corpus

| What must be true | Increment | Where it is checked |
|---|---|---|
| the text-layer corpus regenerates byte-identically | I2 | `tests/test_pdf_corpus.py::test_regeneration_is_reproducible` |
| the scanned corpus regenerates within tolerance | I2 | `tests/test_pdf_corpus.py::test_scanned_regeneration_within_tolerance` |
| the corpus cannot silently shrink or balloon | I2 | `tests/test_pdf_corpus.py::test_stratum_counts_and_page_counts_match_the_plan`, `tests/test_pdf_corpus.py::test_byte_budget` |
| the named paid twins exist and are five | I2 | `tests/test_pdf_corpus.py::test_named_paid_twins_exist` |
| every fixture has ground truth, and every ground truth a fixture | I2 | `tests/test_pdf_corpus.py::test_every_fixture_has_ground_truth_and_every_ground_truth_a_fixture` |

## Extraction: layout, the reader, quality

| What must be true | Increment | Where it is checked |
|---|---|---|
| character-to-block assembly is unit-tested, not only scored | I3a | `tests/test_extract_layout.py::test_blocks_from_chars_empty_page` and the six `test_blocks_from_chars_*` cases beside it |
| page offsets tile the extracted text exactly **and** anchor to their page's content | I3a | `tests/test_extract_layout.py::assert_extraction_properties` — the shared helper every `test_assemble_*` case asserts through |
| offsets are computed after the length-changing string policy | I3a | `tests/test_extract_layout.py::test_assemble_offsets_are_computed_after_normalise_not_before` |
| the string policy is versioned apart from layout | I3a | `tests/test_extract_layout.py::test_textpolicy_is_pure_and_does_not_import_layout` |
| the pure core imports no PDF library | I3a | `tests/test_extract_layout.py::test_layout_is_pure` |
| …and that import check can actually fail | I3a | `tests/test_extract_layout.py::test_imported_names_catches_a_name_import_of_layout` |
| the pdfium reader refuses corrupt, encrypted, zero-page and oversize files | I3b | `tests/test_extract_pdfium.py::test_corrupt_header_fixture_raises_a_named_error_not_a_crash`, `tests/test_extract_pdfium.py::test_encrypted_file_is_refused_before_any_parse`, `tests/test_extract_pdfium.py::test_zero_page_file_is_an_error_not_an_empty_success`, `tests/test_extract_pdfium.py::test_size_guard_fires_at_256mb` |
| a quality regression fails the build | I3b | `tests/test_extract_quality.py::test_compare_to_baseline_flags_a_regression_beyond_tolerance` |
| a changed exemption is a structural regression, not a quiet pass | I3b | `tests/test_extract_quality.py::test_compare_to_baseline_flags_a_changed_exemption_as_a_structural_regression` |
| a zero denominator reports `None`, never `0.0` | I3b | `tests/test_extract_quality.py::test_rate_value_is_none_not_zero_when_denominator_is_zero` |
| the one spending threshold is fitted from two real bounds, not guessed | I3b | `tests/test_extract_quality.py::test_threshold_from_fractions_is_the_midpoint_of_the_two_bounds`, `tests/test_extract_quality.py::test_threshold_from_fractions_raises_without_a_true_positive` |
| the floor reaches an installed copy, not just the repo | I3b | `tests/test_extract_quality.py::test_floors_toml_is_installed_package_data` |
| a committed floor cannot silently drift from its corpus | I3b | `check.sh`'s `pdf-eval` gate, which runs `quality.check_floor_drift` — `tests/test_check_script.py::test_check_sh_declares_the_pdf_quality_guard` asserts the gate is *invoked*, not that it fires; the firing is `tests/test_extract_quality.py::test_threshold_from_fractions_is_the_midpoint_of_the_two_bounds` on the fitting side |
| a gate that cannot run says so and still exits 0 | I3b | `tests/test_check_script.py::test_the_skip_and_continue_shape_exits_zero` |
| the floor's absence stops the paid path from spending | I7b | `tests/test_extract_pageyield.py::test_with_no_fitted_floor_the_paid_path_refuses_to_spend_at_all` |
| a healthy PDF is not paid for by accident | I7b | `tests/test_extract_pageyield.py::test_the_free_path_refuses_to_pay_for_a_healthy_pdf` |
| …and a genuinely scanned one still gets through | I7b | `tests/test_extract_pageyield.py::test_a_scanned_pdf_is_what_the_pre_check_lets_through` |

## The extraction cache

| What must be true | Increment | Where it is checked |
|---|---|---|
| a cached extraction is never re-parsed | I4 | `tests/test_extract_cache.py::test_a_second_lookup_with_the_same_key_never_calls_extract` |
| a hit never loads the backend at all, not even lazily | I4 | `tests/test_extract_cache.py::test_a_hit_never_calls_extract_at_all_not_even_lazily` |
| a corrupt or wrong-version entry misses rather than crashes | I4 | `tests/test_extract_cache.py::test_a_truncated_cache_file_misses_rather_than_crashes`, `tests/test_extract_cache.py::test_a_wrong_schema_version_misses` |
| the automatic sweep never destroys a paid entry | I4 | `tests/test_extract_cache.py::test_the_sweep_spares_paid_entries_and_reports_them` |
| a cache write failure never fails a successful extraction | I4 | `tests/test_extract_cache.py::test_a_cache_write_failure_never_fails_an_already_successful_extraction` |
| `--clear-cache` never touches `ledger.jsonl` | I4 | `tests/test_sync.py::test_clear_cache_preserves_the_ledger` |
| `--clear-cache` aborts unattended without `--yes` | I4 | `tests/test_sync.py::test_clear_cache_without_yes_and_without_a_tty_aborts` |
| `--yes` does not authorise destroying paid entries | I7c | `tests/test_cli_budget.py::test_yes_alone_cannot_destroy_paid_cache_entries_unattended` |
| `--clear-cache`'s euro figure joins real ledger lines | I7c | `tests/test_extract_claude.py::test_clear_cache_reports_spend_and_confirms` |
| staged pages are invisible to every cache sweep | I7c | `tests/test_extract_claude.py::test_staged_pages_are_invisible_to_every_cache_sweep` |

## Chunking, the index, and coherence

| What must be true | Increment | Where it is checked |
|---|---|---|
| `chunk.text == indexed_text[start:end]` for every PDF chunk | I5 | `tests/test_chunk_pdf.py::test_the_span_invariant_holds_for_every_chunk` |
| no character of an extraction is dropped | I5 | `tests/test_chunk_pdf.py::test_every_character_lands_in_at_least_one_chunk` |
| a chunk straddling a page break records both pages | I5 | `tests/test_chunk_pdf.py::test_a_hyphenation_join_across_a_page_break_produces_a_genuine_two_page_chunk` |
| a non-paged source never carries page numbers | I5 | `tests/test_chunk_pdf.py::test_markdown_and_text_chunks_never_carry_page_numbers` |
| a v0.1 index refuses to open, with a remedy | I5 | `tests/test_store.py::test_a_v1_index_refuses_to_open_and_says_rebuild` |
| a stale **free** extraction refuses the query | I5 | `tests/test_search.py::test_a_changed_free_fingerprint_refuses_the_query` |
| a stale **paid** extraction warns and marks, never refuses | I5 | `tests/test_search.py::test_a_changed_paid_fingerprint_warns_and_marks` |
| an unrecognised backend name warns rather than refusing every query | I5 | `tests/test_search.py::test_an_unrecognised_backend_name_warns_and_does_not_refuse` |
| the coherence check never imports a paid client | I5 | `tests/test_search.py::test_coherence_never_imports_a_paid_client` |
| a free run never overwrites a paid extraction, and a paid run picks up what a free one indexed | I5 | `tests/test_sync.py::test_backend_drift` (six cases) |
| a rebuild cannot destroy paid provenance | I5 | `tests/test_sync.py::test_a_rebuild_preserves_paid_provenance`, `tests/test_sync.py::test_a_rebuild_after_clear_cache_still_preserves_it` |
| a fresh clone with no local cache fails honestly, not falsely | I5 | `tests/test_sync.py::test_a_fresh_clone_with_no_local_cache_or_index_fails_honestly_not_falsely` |
| a v0.2 sidecar merge preserves every key it did not write | I5 | `tests/test_sidecar.py::test_with_extraction_provenance_merges_additively` |

## Money: the core

| What must be true | Increment | Where it is checked |
|---|---|---|
| a call that would breach any window is never made | I6a | `tests/test_budget_core.py::test_exactly_at_the_cap_proceeds_one_cent_more_does_not` |
| the reservation is never below the reconciled actual | I6a | `tests/test_budget_core.py::test_reservation_bounds_every_usage_table` |
| a pair straddling a window edge is attributed once, to its start | I6a | `tests/test_budget_core.py::test_a_pair_straddling_midnight_is_attributed_to_the_start`, `tests/test_budget_core.py::test_a_pair_straddling_a_month_end_is_attributed_to_the_start`, `tests/test_budget_core.py::test_a_pair_straddling_a_dst_transition_is_attributed_correctly` |
| a refusal names every window, not just the first to bind | I6a | `tests/test_budget_core.py::test_the_refusal_names_all_three_windows` |
| a request that cannot fit the context window is caught before the call | I6a | `tests/test_budget_core.py::test_the_context_window_precheck_names_its_limit` |
| an estimate against stale prices is refused | I6a | `tests/test_budget_core.py::test_a_stale_as_of_refuses_to_estimate_and_names_the_remedy` |
| an unaffordable document is refused before the first call | I6a | `tests/test_budget_core.py::test_an_unaffordable_document_is_refused_before_the_first_call` |
| confirmation is once per document, not once per slice | I6a | `tests/test_budget_core.py::test_confirmation_is_once_per_document_not_per_slice` |
| the budget core imports no paid client | I6a | `tests/test_budget_core.py::test_budget_module_is_pure` |
| money is `Decimal` from the manifest, never through `float` | I6a | `tests/test_manifest.py::test_budget_values_parse_as_exact_decimal_not_float` |
| the price table ships in the wheel | I6a | `tests/test_budget_core.py::test_prices_are_installed_package_data` |
| a malformed price table is a startup error, never a silent zero | I6a | `tests/test_budget_core.py::test_a_malformed_prices_toml_is_a_startup_error_not_a_silent_zero`, `tests/test_check_script.py::test_check_sh_declares_the_prices_toml_gate` |

## Money: the ledger

| What must be true | Increment | Where it is checked |
|---|---|---|
| the ledger records no query text or content | I6b | `tests/test_ledger.py::test_the_ledger_stores_no_query_text_and_no_document_content` |
| every ledger line carries its currency and FX provenance | I6b | `tests/test_ledger.py::test_every_line_carries_its_cost_and_the_conversion_that_produced_it` |
| money is quantised once, at write time | I6b | `tests/test_ledger.py::test_money_is_quantised_once_and_below_the_cent` |
| a JSON float for money is rejected rather than silently accepted | I6b | `tests/test_ledger.py::test_a_json_number_for_money_is_rejected_rather_than_silently_floated` |
| an interrupted call leaves a visible unknown outcome | I6b | `tests/test_ledger.py::test_a_process_killed_after_reserving_leaves_a_readable_unknown_outcome` |
| a call that never billed does not permanently consume budget | I6b | `tests/test_ledger.py::test_a_call_that_raises_before_a_response_is_voided_and_consumes_no_headroom` |
| a call that **did** bill is never voided to zero | I6b | `tests/test_ledger.py::test_a_call_that_raises_after_a_response_is_never_voided` |
| a void can never supersede a reconciliation | I6b | `tests/test_ledger.py::test_a_void_can_never_supersede_a_reconciliation` |
| two processes appending at once interleave no record | I6b | `tests/test_ledger.py::test_two_processes_appending_at_once_interleave_no_record` |
| the ledger survives a rebuild and a `--clear-cache` byte for byte | I6b | `tests/test_ledger.py::test_the_ledger_survives_rebuild_and_clear_cache_byte_for_byte` |
| an unresolvable unknown outcome has a documented way out | I6b | `tests/test_ledger.py::test_resolving_an_unknown_outcome_appends_and_never_edits` |
| `pnk budget --resolve` appends rather than edits | I6b | `tests/test_cli_budget.py::test_resolve_closes_an_unknown_outcome_from_the_command_line` |
| a non-interactive run never spends silently, and never aborts with nothing to confirm | I6b | `tests/test_cli_budget.py::test_a_confirmation_owed_with_no_tty_and_no_yes_aborts_with_a_remedy`, `tests/test_cli_budget.py::test_a_non_interactive_run_with_nothing_to_confirm_proceeds` |
| the month's cap stops a run the operation's cap would allow | I6b | `tests/test_cli_budget.py::test_a_kb_at_499_of_a_500_month_refuses_the_next_call` |
| spend is read back from the ledger, never tallied in memory | I6b | `tests/test_cli_budget.py::test_the_operation_window_is_read_back_from_the_ledger_not_tallied_in_memory` |
| hook-driven and CI syncs cannot reach the paid path — proved by running them | I6b | `tests/test_hooks.py::test_hooks_force_the_free_backend`, `tests/test_hooks.py::test_every_hook_and_the_ci_workflow_carry_the_free_backend_flag` |
| the generated CI workflow forces the free backend too | I6b | `tests/test_ci.py::test_the_workflow_forces_the_free_backend`, `tests/test_ci.py::test_the_workflow_and_the_hooks_cannot_disagree` |
| that workflow caches the state directory holding the ledger | I6b | `tests/test_ci.py::test_the_workflow_caches_the_state_directory_that_holds_the_ledger` |
| `pnk init --ci` never overwrites a workflow somebody wrote | I6b | `tests/test_ci.py::test_an_existing_workflow_is_never_overwritten` |

## The paid-path allowlist

| What must be true | Increment | Where it is checked |
|---|---|---|
| the allowlist cannot rot (a listed path must exist) | I7a | `check.sh` gate + `tests/test_paid_path.py::test_the_allowlist_matches_the_source_tree` |
| no paid client is imported outside the allowlist | I7a | `tests/test_paid_path.py::test_no_paid_client_outside_the_allowlist` |
| the allowlist cannot widen (an exclusion cannot exempt a directory) | I7a | `tests/test_paid_path.py::test_a_directory_entry_fails_gate_1`, `tests/test_paid_path.py::test_the_allowlist_exempts_only_the_exact_path` |
| the free path never imports the paid client | I7a | `tests/test_paid_path.py::test_the_free_path_never_imports_the_paid_client` |
| that gate can actually fail | I7a | `tests/test_paid_path.py::test_the_free_path_gate_fails_when_an_import_is_planted` |
| …and says so rather than passing when it cannot run | I7a | `tests/test_paid_path.py::test_the_free_path_gate_says_so_when_it_cannot_run` |
| the two paid-client lists agree | I7a | `tests/test_paid_path.py::test_the_two_paid_client_lists_agree` |
| neither the free CLI nor the MCP server loads the deep client — a server-side loop would spend the *operator's* money on the *caller's* question (DESIGN §4.3) | E3 | `tests/test_paid_path.py::test_the_free_path_and_the_mcp_server_never_load_the_deep_client` |
| …and that gate can fail, which is the only thing that makes "the name is absent" mean anything | E3 | `tests/test_paid_path.py::test_the_deep_client_gate_fails_when_an_import_is_planted` |

## What every paid client obeys (E3)

`src/pinakes/paid.py` — the rules shared by the two allowlisted modules. Not the allowlist itself,
which is the section above; this is what a module that *may* import a client then has to do.

| What must be true | Increment | Where it is checked |
|---|---|---|
| the key is `PINAKES_ANTHROPIC_API_KEY`, stripped, and an ambient `ANTHROPIC_API_KEY` is not enough | E3 | `tests/test_paid.py::test_the_key_is_read_from_the_pinakes_variable_and_stripped`, `tests/test_paid.py::test_an_ambient_anthropic_api_key_is_not_enough`, `tests/test_paid.py::test_a_blank_key_refuses_rather_than_being_sent` |
| a refusal names the **surface** that wanted to spend, so two entry points cannot report each other's | E3 | `tests/test_paid.py::test_the_refusal_names_the_surface_that_wanted_to_spend` |
| the SDK's own retries are off — its default of 2 turns one call into up to three billed requests | E3 | `tests/test_paid.py::test_the_sdk_retries_are_off` |
| a timeout is classified **before** the connection error it subclasses — the ordering that decides void versus unknown outcome, and the one `stubs/anthropic.pyi` warns is easy to get wrong from memory | E3 | `tests/test_paid.py::test_a_timeout_is_classified_before_the_connection_error_it_is_a_subclass_of`, `tests/test_paid.py::test_the_stub_states_the_hierarchy_the_classifier_depends_on` |
| a status error is never billed, and retries only where retrying can help — including a status arriving as something other than an int, which would otherwise crash the comparison on the failure path | E3 | `tests/test_paid.py::test_a_status_error_is_never_billed_and_retries_only_where_retrying_can_help`, `tests/test_paid.py::test_a_status_arriving_as_something_other_than_an_int_does_not_crash_the_comparison` |
| anything the hierarchy does not cover is **billable-unknown** — the safe default, because something nobody classified may have billed | E3 | `tests/test_paid.py::test_an_exception_the_hierarchy_does_not_cover_is_billable_unknown` |

## The paid extractor

| What must be true | Increment | Where it is checked |
|---|---|---|
| a refusal is handled before `content` is read | I7b | `tests/test_extract_claude.py::test_a_refusal_is_handled_before_content_is_read` |
| a refusal reports what the API actually said | I7b | `tests/test_extract_claude.py::test_a_refusal_reports_the_category_and_explanation_the_api_sent` |
| a truncated response is not retried identically | I7b | `tests/test_extract_claude.py::test_a_truncated_response_is_reasked_once_at_the_raised_bound`, `tests/test_extract_claude.py::test_a_second_truncation_is_a_failure` |
| an oversize request fails hard instead of being re-paid | I7b | `tests/test_extract_claude.py::test_a_context_window_failure_is_hard_with_no_retry` |
| a transient failure is retried under a fresh reservation, and the old one is voided | I7b | `tests/test_extract_claude.py::test_a_rate_limit_is_voided_and_retried_under_a_fresh_reservation` |
| a timeout leaves an unknown outcome rather than a void | I7b | `tests/test_extract_claude.py::test_a_timeout_leaves_an_unknown_outcome_rather_than_a_void` |
| a leaked internal tag never reaches the indexed text | I7b | `tests/test_extract_claude.py::test_a_leaked_internal_tag_is_retried_never_stripped` |
| every call, including every retry, is reserved and ledgered | I7b | `tests/test_extract_claude.py::test_every_call_takes_its_own_reservation_and_ledger_pair` |
| the semantic and transport ceilings are separate counters | I7b | `tests/test_extract_claude.py::test_the_semantic_budget_refuses_a_seventh_call`, `tests/test_extract_claude.py::test_transport_attempts_are_bounded_without_consuming_a_schema_retry` |
| a short page array is caught before positional mapping | I7b | `tests/test_extract_claude.py::test_a_short_page_array_is_a_schema_failure`, `tests/test_extract_claude.py::test_parse_refuses_to_map_a_short_array_positionally` |
| the paid backend's page spans are content-anchored, not merely tiling | I7b | `tests/test_extract_claude.py::test_every_pages_own_text_lands_inside_its_own_span`, `tests/test_extract_claude.py::test_page_spans_tile_the_whole_text` |
| offsets are computed after the length-changing string policy | I7b | `tests/test_extract_claude.py::test_normalise_runs_before_offsets` |
| `--estimate-only` generates nothing | I7b | `tests/test_extract_claude.py::test_estimate_only_makes_no_generation_call` |
| the SDK's own retries are disabled — asserted without a stand-in | I7b | `tests/test_extract_claude.py::test_the_client_disables_sdk_retries` (unmarked), `tests/test_extract_claude.py::test_the_real_client_disables_sdk_retries` (`paid`) |
| the reservation is never below the actual | I7b | `tests/test_extract_claude.py::test_reservation_bounds_every_recorded_usage` |
| the reconciliation reads the response, not the reservation | I7b | `tests/test_extract_claude.py::test_the_reconciliation_supersedes_with_the_real_cost_not_the_reservation` |
| changing the model **or K** misses the cache | I7b | `tests/test_extract_claude.py::test_changing_the_model_misses_the_cache`, `tests/test_extract_claude.py::test_changing_k_misses_the_cache` |
| a short final slice is handled | I7b | `tests/test_extract_claude.py::test_a_document_whose_page_count_is_not_a_multiple_of_k` |
| the request shape is pinned, not just the responses | I7b | `tests/test_extract_claude.py::test_the_request_puts_the_document_before_the_text_and_sends_no_sampling_knobs`, `tests/test_extract_claude.py::test_thinking_is_disabled_explicitly_and_pinned_to_its_effort` |
| the recorded-fixture set covers every branch it is cited for | I7b | `tests/test_extract_claude.py::test_the_recorded_fixture_set_covers_every_branch`, `tests/test_extract_claude.py::test_the_branches_a_recording_reached_are_backed_by_one` |
| every fixture says where its bodies came from | I7d | `tests/test_extract_claude.py::test_every_fixture_declares_where_its_bodies_came_from`, `tests/test_extract_claude.py::test_a_recorded_fixture_agrees_with_the_model_it_claims` |
| a cache entry whose `per_page_provenance` is the wrong shape misses, rather than degrading the type | I7b | `tests/test_extract_cache.py::test_a_non_string_provenance_value_misses_rather_than_silently_degrading` |
| the whole wiring works, not only the pieces | I7b | `tests/test_extract_claude.py::test_a_real_sync_extracts_indexes_records_and_caches` |

## The audit, staging, and all-or-nothing commit

| What must be true | Increment | Where it is checked |
|---|---|---|
| a half-extracted document writes nothing rather than a truncated entry | I7c | `tests/test_extract_claude.py::test_a_partially_extracted_document_writes_no_complete_entry` |
| a page with no native layer is exempt, never scored zero | I7c | `tests/test_extract_audit.py::test_a_page_with_no_native_layer_is_exempt_not_zero` |
| an all-exempt document reports no median rather than zero | I7c | `tests/test_extract_audit.py::test_an_all_exempt_document_reports_no_median_rather_than_zero` |
| the audit's summary always carries its denominators | I7c | `tests/test_extract_audit.py::test_the_summary_always_carries_its_denominators` |
| a page-count mismatch refuses rather than zipping to the shorter | I7c | `tests/test_extract_audit.py::test_a_page_count_mismatch_refuses_rather_than_zipping_to_the_shorter` |
| a uniform document flags nothing — "below median" is strict | I7c | `tests/test_extract_audit.py::test_below_median_is_strict_so_a_uniform_document_flags_nothing` |
| an unparsable audit value degrades to exempt, never to a pass | I7c | `tests/test_extract_audit.py::test_an_unparsable_audit_value_degrades_to_exempt` |
| the audit survives the round trip through sidecar provenance | I7c | `tests/test_extract_audit.py::test_the_audit_round_trips_through_provenance` |
| an interrupted paid run re-pays for nothing staged | I7c | `tests/test_extract_claude.py::test_a_resumed_run_re_asks_nothing_that_was_staged` |
| a slice interrupted mid-flight is re-asked whole | I7c | `tests/test_extract_claude.py::test_a_slice_interrupted_mid_flight_is_re_asked_whole` |
| a successful document leaves no staging behind | I7c | `tests/test_extract_claude.py::test_a_successful_document_leaves_no_staging_behind` |
| `--force` alone cannot discard a paid extraction | I7c | `tests/test_sync.py::test_force_alone_without_an_explicit_extract_does_not_override` |
| `--force` widens no cap | I7c | `tests/test_extract_claude.py::test_force_does_not_widen_a_budget_cap` |
| `on_exceed = "partial"` keeps completed documents and stops cleanly | I7c | `tests/test_extract_claude.py::test_on_exceed_partial_is_corpus_level_never_page_level` |
| a corpus stops at the first cap breach rather than failing every document | I7c | `tests/test_extract_claude.py::test_a_corpus_stops_at_the_first_cap_breach_rather_than_failing_every_document` |
| every new `pnk sync` flag has a stated scope in `--help` | I7c | `tests/test_cli.py::test_every_sync_flag_documents_its_scope` |

## Page citations and the health check (I8)

| What must be true | Increment | Where it is checked |
|---|---|---|
| a table-cell word survives extraction → cache → chunk → FTS → CLI **and** MCP | I8 | `tests/test_pdf_trace.py::test_a_table_cell_word_survives_every_hop` |
| every filter dimension actually selects PDF rows when filtered on | I8 | `tests/test_pdf_trace.py::test_every_filter_dimension_resolves_for_pdfs` |
| one slice's cost survives estimate → reservation → usage → reconciliation → report | I8 | `tests/test_pdf_trace.py::test_a_paid_slice_traces_from_estimate_to_the_budget_report` |
| page provenance reaches the MCP surface, not only the CLI | I8 | `tests/test_serve.py::test_mcp_search_carries_page_spans`, `tests/test_serve.py::test_mcp_get_is_page_aware` |
| a chunk spanning two pages renders as a range | I8 | `tests/test_search.py::test_a_two_page_chunk_renders_a_range` |
| a paged citation cannot be misread as character offsets | I8 | `tests/test_search.py::test_the_page_marker_is_what_stops_a_citation_being_ambiguous` |
| a non-paged source keeps the citation it always had | I8 | `tests/test_search.py::test_a_non_paged_source_still_cites_character_offsets`, `tests/test_cli_search.py::test_a_non_paged_source_reports_null_pages_and_the_offset_citation` |
| a PDF is served as extracted text, not as its bytes | I8 | `tests/test_serve.py::test_a_pdf_is_served_as_its_extracted_text_rather_than_its_bytes` |
| a swept extraction cache is an error, never a silent re-extraction | I8 | `tests/test_serve.py::test_a_swept_extraction_cache_is_an_error_rather_than_a_silent_re_extraction` |
| a non-paged source carries `page_start: null` rather than omitting the field — an agent must not have to tell *no pages* from *field missing* | I8 | `tests/test_serve.py::test_a_non_paged_source_carries_null_pages_on_the_mcp_surface` |
| a page range outside the document is refused against its own bounds, saying how many pages it has and that they are 1-indexed | I8 | `tests/test_serve.py::test_a_page_range_outside_the_document_is_refused_by_its_own_bounds` |
| a page range asked of a source that has no pages is refused as such | I8 | `tests/test_serve.py::test_a_page_range_on_a_source_that_has_none_is_refused` |
| a low-yield **page** is flagged inside a healthy document | I8 | `tests/test_doctor.py::test_text_yield_flags_pages_not_documents` |
| the yield floor separates empty from non-empty, and nothing finer | I8 | `tests/test_extract_pageyield.py::test_a_page_exactly_on_the_floor_is_not_below_it`, `tests/test_extract_pageyield.py::test_the_decision_is_per_document_even_though_the_floor_is_per_page` |
| an unmeasurable document is never reported as one that passed | I8 | `tests/test_doctor.py::test_a_partly_swept_cache_still_names_what_it_could_not_measure` |
| the health check does not crash on a KB it does not understand | I8 | `tests/test_doctor.py::test_an_unknown_extraction_backend_does_not_crash_the_health_check` |

## `pnk init` keeps `.pinakes/` out of the repository

| What must be true | Increment | Test |
|---|---|---|
| the check answers what **git** answers, not what the `.gitignore` text looks like — six files measured against real git, four of which the substring test got wrong in one direction or the other | — | `tests/test_init.py::test_the_gitignore_check_answers_what_git_answers` |
| **ignoring part of `.pinakes/` is not protection.** `git check-ignore` exits 0 when *any* argument is ignored, so a rule naming only the ledger would otherwise read as full protection while the index stayed tracked | — | `tests/test_init.py::test_ignoring_only_part_of_pinakes_is_not_protection` |
| protection that lives outside `.gitignore` still counts — `.git/info/exclude`, a global excludes file, a parent repository's rules. **No amount of reading `.gitignore` can see any of them**, so this test fails against any implementation that reads the file rather than asking git | — | `tests/test_init.py::test_protection_that_lives_outside_gitignore_is_still_protection` |
| **the probes are a cover of the directory, not a list of filenames.** A `.gitignore` carrying `*.db` and `*.json` ignores every named file while leaving `index.db-wal` — megabytes of verbatim document text in WAL mode — tracked; so does `.pinakes/*` with `!.pinakes/cache`. Both are in the matrix, because probing three named files was a **regression** against the substring test, which warned there | — | `tests/test_init.py::test_the_gitignore_check_answers_what_git_answers` |
| outside a git repository git is still asked, in a scratch one — so `!.pinakes/` warns and `/.pinakes/` does not, neither of which a text scan got right | — | `tests/test_init.py::test_outside_a_repository_git_is_asked_in_a_scratch_repository` |
| **the *ignore* check fires for an adopted `.gitignore` only** — re-examining one `init` just wrote cannot change its answer, since the file it would read is the file it wrote. **This says nothing about the *index* check, which deliberately fires either way** (rows below): the narrowing was once justified by *"it reaches only the case where a path is already in the index, where the remedy is already satisfied"*, and that reason was wrong — a path already in the index is not a satisfied remedy, it is a second question, and adding an ignore line does not answer it | — | `tests/test_init.py::test_a_gitignore_written_by_init_is_not_re_examined` |
| an ambient `GIT_DIR`/`GIT_WORK_TREE` cannot answer for a different repository — git honours both over `cwd`, and exports them to every hook it runs | — | `tests/test_init.py::test_an_ambient_git_dir_cannot_answer_for_another_repository` |
| a `.gitignore` that is not valid UTF-8, and a `git` that never returns, both degrade to an answer rather than a traceback — `pinakes.toml` is already on disk, so raising leaves a KB the next `pnk init` refuses as "already a KB" | — | `tests/test_init.py::test_a_gitignore_that_is_not_utf8_does_not_abort_a_half_written_kb`, `tests/test_init.py::test_a_git_that_never_returns_does_not_hang_init` |
| **the printed remedy never instructs an action that would not change the verdict.** A `.gitignore` reading `.pinakes/` then `!.pinakes/` is unprotected *with* the line already in it, and *"add this line"* would send the user to do nothing and learn nothing. Only reachable since the check became git's answer rather than a substring test, under which the string's presence **was** the verdict | — | `tests/test_init.py::test_the_remedy_is_only_offered_when_it_would_change_the_verdict`, `tests/test_init.py::test_the_warning_never_tells_you_to_add_a_line_you_already_have` |
| **the command the warning suggests actually prints something.** It is extracted from the printed text, run, and its output checked — asserting that a message *mentions* a command is not a test that the command helps, which is how `git check-ignore -v` shipped: it reports only positively-matched paths, and the branch that named it fires precisely because the path is not matched | — | `tests/test_init.py::test_the_command_the_warning_suggests_actually_prints_something` |
| a `GIT_CEILING_DIRECTORIES` the user set is **honoured**, not scrubbed — it limits git's upward search rather than redirecting it, so obeying it is what makes this check agree with the same user's `git add` | — | `tests/test_init.py::test_a_ceiling_the_user_set_is_honoured_rather_than_scrubbed` |
| a machine with no `git` on PATH still stamps a KB — `init` has never required it, and refusing over a missing version-control tool would be a worse failure than the one this fixes | — | `tests/test_init.py::test_init_still_stamps_a_kb_when_git_is_not_installed` |
| **a `.pinakes/` already in the index is reported even when git ignores it.** Ignoring a directory does not untrack what is in it, so the ledger and every deep transcript keep being committed while the ignore check reports *protected* — measured 20260825, the detector returned `True` for a repository committing the user's verbatim questions | — | `tests/test_init.py::test_a_tracked_pinakes_is_reported_even_when_git_ignores_it`, `tests/test_init.py::test_a_staged_but_never_committed_pinakes_is_already_tracked` |
| **the index question is asked whether or not the `.gitignore` was adopted.** It is a question about the index, not about the ignore file's provenance — and the state it exists for is most often a repository with no `.gitignore` at all, where `init` writes one and the adopted-only gate would skip it | — | `tests/test_init.py::test_a_tracked_pinakes_is_reported_when_init_writes_the_gitignore` |
| **the index question is scoped absolutely and literally** — `:(literal)` plus the resolved root. Defence rather than a fixed bug: `_ask_git` pins git's cwd to `root`, so a relative pathspec answers identically today, and **the assertion is on the pathspec because a behavioural test cannot fail** — mutated to the relative form, 68 of 69 tests in this module still passed | — | `tests/test_init.py::test_the_index_question_is_scoped_absolutely_and_literally` |
| **unknown is not clean.** Outside a repository, or when git cannot answer, the index question yields *unknown* rather than *nothing tracked*. Asserted below the reporting surface: the reported field is a `bool`, so `None` and `False` collapse into it and an implementation returning `False` passes every test through `init` | — | `tests/test_init.py::test_outside_a_repository_nothing_is_claimed_about_tracking`, `tests/test_init.py::test_an_unanswerable_index_question_is_unknown_rather_than_clean` |
| a repository that tracks nothing under `.pinakes/` reports nothing — the ordinary healthy state stays silent | — | `tests/test_init.py::test_a_repository_that_tracks_nothing_reports_nothing_tracked` |
| **the untrack remedy says index-not-disk, and claims nothing about pushed history.** `git rm -r --cached` leaves every file byte-readable where it is, and cannot change a commit already pushed — the text states the limit rather than implying the exposure is undone | — | `tests/test_init.py::test_the_tracked_remedy_says_index_not_disk_and_claims_nothing_about_pushed_history` |
| **when the ignore rule is missing too, the remedy puts the line before the untrack.** Reversed, the next ordinary `git add -A` re-stages what `git rm --cached` just removed — measured — so a remedy whose steps are right and whose order is wrong fails silently | — | `tests/test_init.py::test_when_the_rule_is_missing_too_the_remedy_puts_the_line_before_the_untrack` |

## `pnk doctor`, check by check

| What must be true | Increment | Where it is checked |
|---|---|---|
| **every check `diagnose` can produce is named by a test** | I9 | `tests/test_doctor.py::test_every_doctor_check_is_exercised_by_a_test` |
| a non-OK check carries a remedy — **spot-checked on five, not enumerated** | I11 | `tests/test_doctor.py::test_every_problem_carries_a_remedy` asserts over whichever checks are non-OK in one unsynced fixture (5 of 18 there; `diagnose` produces ≥29 on a synced KB), so a new remedy-less WARN passes unless it fires in that fixture. The enumerating sibling is `tests/test_doctor.py::test_every_doctor_check_is_exercised_by_a_test` |
| the template check reports drift without applying anything | I9 | `tests/test_doctor.py::test_a_template_version_drift_is_reported_with_both_versions`, `tests/test_doctor.py::test_a_template_the_install_does_not_have_is_a_warning_not_a_failure` |
| drift is reported as a **computed** line count, never a constant | T2 | `tests/test_doctor.py::test_a_kb_recording_an_older_template_version_reports_the_line_count` |
| **nothing the user wrote reaches the report** — a rendered value cancels on both sides, a literal enters neither | T2 | `tests/test_doctor.py::test_a_user_edited_manifest_value_never_appears_in_the_template_drift_report` |
| a comment-only template change is still reported — the live gap (F3) is entirely comments | T2 | `tests/test_doctor.py::test_a_comment_only_template_change_is_reported` |
| the `[kb]` identity block never produces a hunk, so T4's `--apply` cannot refuse for everyone | T2 | `tests/test_doctor.py::test_the_kb_identity_block_never_produces_a_hunk` |
| an unarchived recorded version says *cannot compare*, with a remedy naming the manual comparison | T2 | `tests/test_doctor.py::test_an_unarchived_recorded_version_says_it_cannot_compare_rather_than_ok` |
| a version bump that leaves the manifest alone says *same manifest*, never `0 lines differ` | T2 | `tests/test_doctor.py::test_a_version_bump_that_leaves_the_manifest_alone_does_not_report_zero_lines` |
| the *cannot compare* remedy promises nothing a later release cannot keep | T2 | `tests/test_doctor.py::test_the_cannot_compare_remedy_promises_nothing_a_later_release_cannot_keep` |
| a template version needing an unknown variable refuses with a **message**, not a traceback | T2 | `tests/test_doctor.py::test_a_template_version_needing_an_unknown_variable_refuses_with_a_message`, `tests/test_init.py::test_a_template_variable_that_is_never_supplied_fails_loudly` |
| `pnk doctor` on a current KB renders nothing | T2 | `tests/test_doctor.py::test_a_template_with_no_drift_reports_ok_and_renders_nothing` |
| an archived version needing a variable the current one dropped still renders (the union context) | T2 | `tests/test_doctor.py::test_an_archived_version_needing_a_variable_the_current_one_dropped_still_renders` |
| the gate's leg (vi) context and the product's `render_context` cannot drift apart | T2 | `tests/test_template_drift.py::test_render_context_supplies_exactly_the_declared_union` |
| a disabled reranker is reported as configured, not as missing | I9 | `tests/test_doctor.py::test_the_reranker_check_says_when_reranking_is_off_rather_than_loading_one` |
| the model cache check names where weights resolve | I9 | `tests/test_doctor.py::test_the_model_cache_check_names_the_directory_weights_resolve_under` |
| an unavailable extension loader says what it does *not* affect | I9 | `tests/test_doctor.py::test_the_extensions_check_explains_that_it_only_gates_an_unshipped_tier` |
| a dangling link inside the KB is a warning | I9 | `tests/test_doctor.py::test_a_dangling_link_inside_this_kb_is_a_warning_naming_how_many` |
| link coverage is the **ratio**, not the edge count | L7 | `tests/test_doctor.py::test_link_coverage_reports_the_ratio_not_the_edge_count` |
| ...counting authored links only, never reverse-scanned rows | L7 | `tests/test_doctor.py::test_link_coverage_counts_authored_links_only` |
| a KB with no authored links nudges | L7 | `tests/test_doctor.py::test_a_kb_with_no_authored_links_nudges` |
| a dangling cross-KB target warns, when its KB is here to ask | L7 | `tests/test_doctor.py::test_a_dangling_cross_kb_target_warns_with_a_reason` |
| ...and one its own KB does have is not unresolved | L7 | `tests/test_doctor.py::test_a_cross_kb_target_that_its_own_kb_does_have_is_not_unresolved` |
| ...while a KB absent from this machine is counted, not judged | L7 | `tests/test_doctor.py::test_a_cross_kb_link_into_a_kb_not_here_is_counted_but_not_called_unresolved` |
| a linked KB absent from this machine warns | L7 | `tests/test_doctor.py::test_a_linked_kb_absent_from_this_machine_warns` |
| ...one whose path resolves to nothing warns with the reason | L7 | `tests/test_doctor.py::test_a_linked_kb_path_that_resolves_to_nothing_warns_with_the_reason` |
| ...and an absolute path warns even when it resolves | L7 | `tests/test_doctor.py::test_an_absolute_linked_kb_path_warns` |
| the linked-KBs check exists even with none declared, so the coverage guard sees it | L7 | `tests/test_doctor.py::test_a_kb_declaring_no_linked_kbs_still_produces_the_check` |
| ...and runs without an index, when an absolute path matters most | L7 | `tests/test_doctor.py::test_the_linked_kbs_check_runs_without_an_index` |
| an unsynced KB says the link checks did not run | L8 | `tests/test_doctor.py::test_an_unsynced_kb_says_the_link_checks_did_not_run` |
| a soft-deleted document does not inflate the coverage ratio | L7 review | `tests/test_doctor.py::test_a_deleted_document_leaves_the_coverage_ratio_honest` |
| doctor writes nothing into a partner KB (§6.2) | L7 review | `tests/test_doctor.py::test_doctor_writes_nothing_into_a_partner_kb` |
| ...and answers from a partner with no index at all | L7 review | `tests/test_doctor.py::test_a_partner_without_an_index_still_answers` |
| a cross-KB target resolves against the partner's **own** `[kb] id` | L7 review | `tests/test_doctor.py::test_a_cross_kb_target_is_resolved_against_the_partners_own_id`, `::test_a_partner_is_found_by_its_own_id_even_when_the_manifest_declares_another` |
| an incomplete partner walk is never used as evidence of absence | L7 review | `tests/test_doctor.py::test_a_partner_whose_sidecars_cannot_all_be_read_is_not_used_as_evidence`, `::test_a_partner_whose_sources_are_unusable_is_not_used_as_evidence` |
| an internal link is not counted as cross-KB | L7 review | `tests/test_doctor.py::test_an_internal_link_is_not_counted_as_cross_kb` |
| a `~` linked-KB path is warned as absolute | L7 review | `tests/test_doctor.py::test_a_tilde_linked_kb_path_is_warned_as_absolute` |
| an unreadable linked-KB path is a warning, not a traceback | L7 review | `tests/test_doctor.py::test_an_unreadable_linked_kb_path_is_a_warning_not_a_traceback` |
| ...and an unusable partner `roots` entry likewise | L7 review 2 | `tests/test_doctor.py::test_a_partner_roots_entry_that_cannot_be_resolved_is_not_a_traceback` |

## The evaluation is reproducible (G1)

| What must be true | Increment | Where it is checked |
|---|---|---|
| the same index evaluated twice gives the same answers | G1 | `tests/test_search_reproducibility.py::test_outcomes_are_identical_across_repeated_runs` |
| an incremental sync and a `--rebuild` agree question by question | G1 | `tests/test_search_reproducibility.py::test_outcomes_survive_an_incremental_sync_and_rebuild`, and `check.sh`'s `eval-reproducibility` gate over four kinds of corpus change |
| ...and so does a first sync of a fresh clone | G1 | `tests/test_search_reproducibility.py::test_outcomes_survive_a_sync_from_scratch` |
| the two sync paths really do assign different rowids, so the rows above are not vacuous | G1 | `tests/test_search_reproducibility.py::test_the_two_sync_paths_really_do_assign_different_rowids` |
| the vector array is ordered on something a rebuild preserves | G1 | `tests/test_search_reproducibility.py::test_load_vectors_returns_corpus_order_not_rowid_order` |
| a BM25 tie is cut the same way every time | G1 | `tests/test_search_reproducibility.py::test_the_lexical_cut_keeps_the_same_chunk_when_scores_tie` |
| hydration orders two chunks of the *same* document, which the `p.path` tiebreak cannot | G1 | `tests/test_search_reproducibility.py::test_hydration_returns_corpus_order_whatever_order_it_is_asked_in` |
| adding a document does not reorder tied results elsewhere | G1 | `tests/test_search_reproducibility.py::test_a_tied_ranking_is_unmoved_by_documents_added_elsewhere` |
| two machines answer every question the same way | G1 | CI's `eval-cross-machine` and `eval-cross-machine-compare` jobs; `tests/test_check_script.py::test_ci_compares_per_question_outcomes_across_two_operating_systems` asserts both legs are still there |
| the gate is invoked, and can still fail | G1 | `tests/test_check_script.py::test_check_sh_declares_the_eval_reproducibility_gate`, `tests/test_check_script.py::test_ci_runs_the_eval_reproducibility_gate_and_proves_it_can_fail` |

## The manifest compatibility floor (G4)

| What must be true | Increment | Where it is checked |
|---|---|---|
| the floor is read **before** strict validation | G4 | `tests/test_manifest_compat.py::test_the_pre_pass_runs_before_strict_validation` |
| a KB needing a newer Pinakes names both versions | G4 | `tests/test_manifest_compat.py::test_a_manifest_requiring_a_newer_pinakes_names_the_version` |
| an absent floor is not an error | G4 | `tests/test_manifest_compat.py::test_an_absent_requires_pinakes_is_not_an_error` |
| a floor this build exactly meets is accepted | G4 | `tests/test_manifest_compat.py::test_a_floor_this_build_meets_exactly_is_accepted`, `tests/test_manifest_compat.py::test_a_shorter_floor_compares_as_the_same_version`, `tests/test_manifest_compat.py::test_a_longer_floor_of_trailing_zeros_is_the_same_version` |
| only a floor is accepted — no ceiling, no bare version | G4 | `tests/test_manifest_compat.py::test_a_floor_that_is_not_a_lower_bound_is_refused` |
| a version that is not dotted ASCII digits is refused, not compared | G4 | `tests/test_manifest_compat.py::test_a_floor_that_is_not_a_dotted_number_is_refused` |
| the field does not trip the unknown-key check it exists to explain | G4 | `tests/test_manifest_compat.py::test_the_field_does_not_trip_the_unknown_key_check` |
| the pre-pass reports one error, never a second one for the same mistake | G4 | `tests/test_manifest_compat.py::test_a_missing_or_non_table_kb_is_left_to_the_strict_validator` — asserts the strict validator's *exact* wording, because a keyword match survived a deliberately duplicated pre-pass error |
| a version component too long for `int()` is refused, not a traceback | G4 | `tests/test_manifest_compat.py::test_a_version_component_of_absurd_length_is_refused_not_a_traceback` |
| whitespace around the version is refused, as the digits already were | G4 | `tests/test_manifest_compat.py::test_whitespace_around_the_version_is_refused` |
| a leading zero compares as the number it is | G4 | `tests/test_manifest_compat.py::test_a_leading_zero_compares_as_the_number_it_is` |
| a non-string value names the TOML type, never a Python repr | G4 | `tests/test_manifest_compat.py::test_a_non_string_value_names_the_toml_type_not_a_python_repr` |
| an unparseable `__version__` skips the check instead of crashing every command | G4 | `tests/test_manifest_compat.py::test_an_unparseable_own_version_skips_the_check_rather_than_crashing` |
| `pnk init` stamps no floor | G4 | `tests/test_manifest_compat.py::test_the_template_does_not_stamp_a_floor` |

## The golden set, per question (G2)

| What must be true | Increment | Where it is checked |
|---|---|---|
| the committed golden set is well formed, and its two decisive classes are the size the plan set | G2 | `tests/test_eval.py::test_the_committed_golden_set_is_well_formed` |
| per-question outcomes exist as an artifact, and re-score to the same aggregates | G2 | `tests/test_eval.py::test_per_question_outcomes_round_trip` |
| every field a row carries reaches a metric | G2 | `tests/test_eval.py::test_a_row_carries_everything_every_metric_needs` |
| the committed artifact and the committed baseline describe one run | G2 | `tests/test_eval.py::test_the_committed_artifact_describes_the_committed_baseline` |
| growing the set moved no question already in it | G2 | `tests/test_eval.py::test_the_committed_41_score_exactly_their_pre_growth_values` |
| an unknown or absent `kind` is refused, never defaulted | G2 | `tests/test_eval.py::test_an_unknown_kind_is_refused` |
| a repeated id is refused, and an absent one is derived | G2 | `tests/test_eval.py::test_a_repeated_id_is_refused`, `tests/test_eval.py::test_an_absent_id_is_derived_from_the_question` |
| an empty question set skips with a printed reason instead of failing | G2 | `tests/test_eval.py::test_an_empty_question_set_skips_with_a_reason` |
| a file whose `questions` key is missing is still refused, so the skip cannot swallow a typo | G2 | `tests/test_eval.py::test_a_file_with_no_questions_key_is_still_refused` |
| a row missing a field is refused by name, never a bare `KeyError` | G2 | `tests/test_eval.py::test_a_row_missing_a_field_is_refused_by_name` |
| the channel-reachable ceiling is measured before the schema bumps | G2 | `tests/test_eval.py::test_the_reachable_ceiling_probe_needs_no_index_schema_change` |
| the probe answers to the edge set, rather than reporting the same number whatever the graph holds | G2 | `tests/test_eval.py::test_the_reachable_ceiling_probe_answers_to_the_edge_set` |
| a kind that derives zero edges is a key in the census at `0`, never omitted | G2 | `tests/test_eval.py::test_a_kind_that_derives_zero_edges_is_reported_not_omitted` |
| a kind dropped via `--drop` shows `0` in both the printed table and `--json`, alongside every other kind | G2 | `tests/test_eval.py::test_a_dropped_kind_shows_zero_in_both_output_formats` |
| the per-kind edge census reconciles with the `Graph` it describes, for every derived kind | G2 | `tests/test_eval.py::test_edge_census_reconciles_with_the_graph_it_describes` |
| a hop expecting a path the index does not hold refuses the run by name, instead of being counted failing-and-unreachable | G2 | `tests/test_eval.py::test_the_probe_refuses_a_hop_expecting_a_document_the_index_does_not_hold` |
| a `multi-hop` question with no `hops` refuses the run by name, instead of padding the denominator it can never fail | G2 | `tests/test_eval.py::test_the_probe_refuses_a_multi_hop_question_with_no_hops` |
| a `multi-hop` question with one hop refuses too — the shape that moves `liftable` **upward**, against a precondition that is a floor | G2 | `tests/test_eval.py::test_the_probe_refuses_a_multi_hop_question_carrying_a_single_hop` |
| a hop expecting a document the index holds **no chunks** for refuses: a correctly spelled path that can never land or be reached | G2 | `tests/test_eval.py::test_the_probe_refuses_a_hop_expecting_a_document_the_index_holds_no_chunks_for` |
| a hop with an empty `query` refuses, rather than failing on its own terms and being counted | G2 | `tests/test_eval.py::test_the_probe_refuses_a_hop_whose_query_is_empty` |
| a golden set with no `multi-hop` question refuses, rather than printing zeros that read as a measurement | G2 | `tests/test_eval.py::test_the_probe_refuses_a_golden_set_with_no_multi_hop_question_at_all` |
| `filters` that admit no document, or that exclude the last hop's own `expect`, refuse — they are applied to the hop that decides the verdict | G2 | `tests/test_eval.py::test_the_probe_refuses_filters_that_admit_nothing`, `tests/test_eval.py::test_the_probe_refuses_filters_that_exclude_the_last_hops_own_document` |
| a question-level `expect` naming nothing refuses, and the message says it moves no figure — the probe measures hops | G2 | `tests/test_eval.py::test_a_question_level_expect_that_names_nothing_is_refused_and_said_to_move_no_figure` |
| a refusal names the spelling the index holds, and which invisible difference it is — pinned on letter case and a leading `./`; the NFC/NFD branch shares the mechanism and no committed corpus can exercise it | G2 | `tests/test_eval.py::test_a_path_wrong_only_in_case_is_refused_with_the_indexed_spelling` |
| the artifact identifies all three inputs the numbers are a function of — the corpus, the golden set (path + sha256 + counts) and the pipeline down to model and revision | G2 | `tests/test_eval.py::test_the_artifact_records_the_configuration_that_produced_the_numbers` |
| a hop problem on a question the probe never measures says no figure moves, in a whole sentence | G2 | `tests/test_eval.py::test_a_hop_problem_on_a_question_the_probe_never_measures_says_so` |
| a mistyped path is reported once, and never blamed on a healthy `filters:` block | G2 | `tests/test_eval.py::test_a_mistyped_path_is_not_also_blamed_on_the_filters` |
| two hops that are the same retrieval (same `expect`, `query` differing only in case or spacing) refuse — one retrieval written twice clears the hop floor and can move `liftable` upward | G2 | `tests/test_eval.py::test_the_probe_refuses_a_question_whose_two_hops_are_identical` |
| a well-formed golden set is not refused — the control that keeps every refusal from being caused by the environment | G2 | `tests/test_eval.py::test_a_well_formed_golden_set_is_not_refused` |
| `--fake` and `--kb` cannot be combined, so no run can label one corpus's numbers with another's | G2 | `tests/test_eval.py::test_the_probe_refuses_fake_together_with_kb` |
| the output names the KB measured — pinned against a KB that is **not** the demo one, so the test can detect "always names the default" | G2 | `tests/test_eval.py::test_the_probe_names_the_kb_it_measured` |
| a `--fake` run names its own copy and records that a fake backend produced the numbers | G2 | `tests/test_eval.py::test_the_fake_run_names_its_own_copy_and_says_it_is_fake` |

## The node model and the edge set (G3)

| What must be true | Increment | Where it is checked |
|---|---|---|
| a chunk node is keyed on `<doc-ulid>:<ordinal>`, not on `chunks.id` | G3 | `tests/test_edges.py::test_a_chunk_node_is_keyed_on_the_document_ulid_and_ordinal` |
| ...and that key survives a rebuild, which the rowid does not | G3 | `tests/test_edges.py::test_a_chunk_node_key_survives_a_rebuild` |
| heading nodes are scoped per document | G3 | `tests/test_edges.py::test_a_heading_node_is_scoped_to_its_document`, `tests/test_edges.py::test_a_heading_hub_never_connects_two_documents` |
| a document at the KB root still has a directory hub | G3 | `tests/test_edges.py::test_a_document_at_the_kb_root_still_has_a_directory_hub` |
| hub edges stay linear, not quadratic | G3 | `tests/test_edges.py::test_a_shared_tag_produces_linear_not_quadratic_edges` |
| one row per spoke, hub always as `src` | G3 | `tests/test_edges.py::test_a_hub_spoke_is_stored_once_not_twice` |
| a tag repeated in one sidecar is one spoke | G3 | `tests/test_edges.py::test_a_duplicate_tag_in_one_sidecar_is_one_spoke` |
| a hub with a single member is not minted — it connects nothing | G3 | `tests/test_edges.py::test_a_hub_with_a_single_member_is_not_minted` |
| hub damping follows the corpus with no stored degree | G3 | `tests/test_edges.py::test_a_dropped_tag_lowers_the_divisor` |
| weight across a hub is the product of both spokes | G3 | `tests/test_edges.py::test_weight_across_a_hub_is_the_product_of_both_spokes` |
| a hub is entered from a member and expanded from the hub — the two halves are different queries | G3 | `tests/test_edges.py::test_a_hub_is_entered_from_a_member_and_expanded_from_the_hub` |
| `sibling` joins adjacent ordinals, stored lower→higher | G3 | `tests/test_edges.py::test_sibling_edges_join_adjacent_ordinals` |
| ...and never crosses a document | G3 | `tests/test_edges.py::test_a_sibling_edge_never_crosses_a_document` |
| hierarchy is derived by `heading_path` prefix, stored parent→child | G3 | `tests/test_edges.py::test_parent_and_child_follow_heading_path_prefixes` |
| ...on path segments, so a heading that is a string prefix is not a parent | G3 | `tests/test_edges.py::test_a_sibling_heading_that_is_a_string_prefix_is_not_a_parent` |
| `membership` runs document → chunk | G3 | `tests/test_edges.py::test_membership_runs_document_to_chunk` |
| a symmetric edge is reachable from both ends | G3 | `tests/test_edges.py::test_a_symmetric_edge_is_reachable_from_both_ends` |
| a soft-deleted document leaves no edges, and empties its hubs | G3 | `tests/test_edges.py::test_a_soft_deleted_document_leaves_no_edges` |
| an authored edge is read from `links` and never copied into `edges` | G3 | `tests/test_edges.py::test_an_authored_edge_is_read_from_links_and_never_stored_in_edges` |
| ...keeping the direction the sidecar wrote it | G3 | `tests/test_edges.py::test_an_authored_row_keeps_the_direction_the_sidecar_wrote_it` |
| ...and a cross-KB row never enters the channel, in either direction | G3 | `tests/test_edges.py::test_a_cross_kb_authored_row_never_enters_the_channel` |
| the derived kind set is selectable at read time, so G5's arms need no rebuild | G3 | `tests/test_edges.py::test_dropping_a_kind_removes_it_from_every_read`, `tests/test_edges.py::test_dropping_authored_removes_it_without_a_rederivation` |
| an unknown kind name is refused rather than dropping nothing | G3 | `tests/test_edges.py::test_an_unknown_kind_name_is_refused_rather_than_dropping_nothing` |
| every kind is a census key, even at zero | G3 | `tests/test_edges.py::test_every_kind_is_a_census_key_even_at_zero` |
| the sync report prints every kind and what deriving them cost | G3 | `tests/test_edges.py::test_the_sync_report_prints_every_kind_with_its_wall_clock` |
| the traversal surface returns documents only, with a structural graph present to leak | G3 | `tests/test_edges.py::test_the_traversal_surface_returns_no_structural_nodes` |
| `pnk links --json` on both corpora is unchanged across the schema bump | G3 | `tests/test_links_surface.py::test_the_authored_links_surface_is_unchanged_by_the_schema_bump`, `tests/test_links_surface.py::test_the_fixture_covers_both_corpora_and_holds_real_neighbours` |
| a `schema_version` 2 index is refused with a remedy | G3 | `tests/test_edges.py::test_a_schema_version_2_index_is_refused_with_its_remedy`, `tests/test_store.py::test_schema_version_is_3_for_g3s_node_and_edge_tables` |
| the stored edge set agrees with the probe the go decision was taken on | G3 | `tests/test_edges.py::test_the_stored_edge_set_agrees_with_the_probe_the_decision_was_taken_on` |
| a forked KB sharing a document ULID does not forge a local authored edge — found by mutation, caught by nothing | G3 | `tests/test_edges.py::test_a_forked_kb_sharing_a_document_ulid_does_not_forge_a_local_authored_edge` |
| the hierarchy lookup derives exactly the naive prefix relation it replaced | G3 | `tests/test_edges.py::test_hierarchy_matches_the_naive_prefix_predicate` |
| asking for `authored` without the local KB is refused, never silently dropped | G3 | `tests/test_edges.py::test_asking_for_authored_without_the_local_kb_is_refused` |
| an empty tag is not a shared value, and a repeated one does not inflate a hub's size | G3 | `tests/test_edges.py::test_an_empty_tag_is_not_a_shared_value`, `tests/test_edges.py::test_one_document_repeating_a_tag_mints_no_hub` |
| `co-located` is the immediate directory, never an ancestor | G3 | `tests/test_edges.py::test_a_nested_directory_is_its_own_hub` |
| a heading containing the path separator is a measured bound, not a belief | G3 | `tests/test_edges.py::test_a_heading_containing_the_separator_is_a_known_bound` |
| `parent-child`'s arity — the product of two sections' chunk counts — is pinned rather than discovered | G3 | `tests/test_edges.py::test_the_hierarchy_row_count_is_pinned_because_it_is_the_product_of_two_sections` |
| the node- and edge-kind constants match the DDL's CHECK constraints, in both directions | G3 | `tests/test_store.py::test_constants_match_the_check_constraints` |
| the deriver is on the free path, and gate 4 reaches it | G3 | `tests/test_paid_path.py::test_the_free_path_never_imports_the_paid_client` |

## The expansion channel and its gate (G5)

| What must be true | Increment | Where it is checked |
|---|---|---|
| `expand` surfaces a document two-list fusion does not return | G5 | `tests/test_graph_channel.py::test_expand_surfaces_a_document_fusion_alone_does_not` |
| an empty edge set reproduces two-list fusion **exactly**, not approximately | G5 | `tests/test_graph_channel.py::test_an_empty_edge_set_reproduces_two_list_fusion_exactly` |
| `off` issues no query against `nodes` or `edges` at all | G5 | `tests/test_graph_channel.py::test_off_issues_no_traversal_query` |
| a same-document chunk reachable **only** by membership never appears | G5 | `tests/test_graph_channel.py::test_a_chunk_reachable_only_by_membership_never_appears` |
| ...and one also reachable by `sibling` is not excluded — the "only" is load-bearing | G5 | `tests/test_graph_channel.py::test_a_same_document_chunk_reachable_by_sibling_is_not_excluded` |
| membership neighbours are dropped before the cut, so they never spend fan-out budget | G5 | `tests/test_graph_channel.py::test_membership_neighbours_do_not_consume_the_fanout_budget` |
| a root is expanded but never emitted — its slot belongs to a chunk fusion has not seen | G5 | `tests/test_graph_channel.py::test_a_root_is_expanded_but_never_emitted` |
| ...and it is dropped **before** the fan-out cut, so it never spends a slot it is then discarded from | G5 | `tests/test_graph_channel.py::test_a_root_does_not_consume_a_fanout_slot` |
| the channel ranks on the cosines `search` computed, not on a map it never received | G5 | `tests/test_graph_channel.py::test_the_channel_ranks_by_the_cosine_search_computed` |
| a two-hop chunk outranks a one-hop one when the query says so, so depth 2 reaches the *output* | G5 | `tests/test_graph_channel.py::test_a_two_hop_chunk_outranks_a_one_hop_one_when_the_query_says_so` |
| ...and link distance still breaks a tie the query cannot | G5 | `tests/test_graph_channel.py::test_distance_breaks_a_tie_the_query_cannot` |
| a document never passes through to itself, even when it is not a root | G5 | `tests/test_graph_channel.py::test_a_document_never_passes_through_to_itself` |
| a root's own document never contributes its chunks, at any depth — a clause 18 mutants left standing | G5 | `tests/test_graph_channel.py::test_a_root_document_never_contributes_its_chunks_at_any_depth` |
| `pnk links --json` is byte-identical with the channel on (decision 16) | G5 | `tests/test_graph_channel.py::test_pnk_links_output_is_unchanged_with_the_channel_on` |
| the gate's two edge-set variants differ in cardinality, so the split discriminates | G5 | `tests/test_graph_channel.py::test_the_gate_is_computed_with_and_without_authored_edges` |
| "without authored" is the whole kind, whatever a row's `origin` | G5 | `tests/test_graph_channel.py::test_dropping_authored_is_every_links_row_regardless_of_origin` |
| the sign test reproduces the plan's table **and** refuses the row above each threshold | G5 | `tests/test_graph_channel.py::test_the_sign_test_reproduces_the_plans_table_and_the_rows_below_it` |
| a rise in `false_confidence` stops the gate — clause 2 cannot see it | G5 | `tests/test_graph_channel.py::test_a_rise_in_false_confidence_stops_the_gate` |
| a newly-found question reported at LOW does not veto the win clause 1 demands | G5 | `tests/test_graph_channel.py::test_a_newly_found_question_at_low_confidence_does_not_veto_the_win` |
| ...while a question that *lost* confidence does stop it — the other half of the decomposition | G5 | `tests/test_graph_channel.py::test_a_question_that_lost_confidence_stops_the_gate` |
| a drop in `confidence_coverage` stops the gate | G5 | `tests/test_graph_channel.py::test_a_drop_in_confidence_coverage_stops_the_gate` |
| **both** runs must pass; one green run licenses nothing | G5 | `tests/test_graph_channel.py::test_the_gate_requires_both_runs_to_pass` |
| a class vanishing stops the gate | G5 | `tests/test_graph_channel.py::test_a_class_vanishing_stops_the_gate` |
| an unpaired question set is refused before any clause is scored | G5 | `tests/test_graph_channel.py::test_an_unpaired_question_set_is_refused_before_any_clause_is_scored` |
| a leg is identified by its header, never its filename | G5 | `tests/test_graph_channel.py::test_a_leg_that_is_not_the_leg_it_was_passed_as_is_refused`, `tests/test_graph_channel.py::test_a_without_authored_leg_that_kept_authored_edges_is_refused` |
| ...and a gate that should pass does pass, so the four above are not green against a gate that refuses everything | G5 | `tests/test_graph_channel.py::test_a_gate_that_passes_reports_that_it_passes` |
| `graph_channel` defaults to `off`, is not stamped into the template, and refuses an unknown name | G5 | `tests/test_graph_channel.py::test_the_default_is_off`, `tests/test_graph_channel.py::test_the_channel_setting_is_not_stamped_into_the_template`, `tests/test_graph_channel.py::test_an_unknown_channel_name_is_refused` |
| a soft-deleted document never reaches the channel — the other end of G3's reaping | G5 | `tests/test_graph_channel.py::test_a_soft_deleted_document_never_reaches_the_channel` |
| an index with no derived nodes walks empty rather than failing | G5 | `tests/test_graph_channel.py::test_a_kb_synced_before_the_edge_set_existed_walks_empty` |
| the committed corpora still measure the two-list pipeline | G5 | `tests/test_graph_channel.py::test_the_corpora_are_left_alone`, `tests/test_graph_channel.py::test_the_workspace_helper_copies_rather_than_edits` |

## Edge-hub reporting (G6)

| What must be true | Increment | Where it is checked |
|---|---|---|
| `pnk doctor` reports the highest-degree structural edge hubs, highest first | G6 | `tests/test_doctor.py::test_edge_hubs_are_reported_highest_degree_first` |
| `pnk doctor` reports what share of chunks carry a heading path | — | `tests/test_doctor.py::test_heading_coverage_is_full_on_an_all_markdown_kb` |
| A source type carrying **no** heading path is reported and named — and only `markdown` at 0% is a WARN, every other type being OK with a note (0.14.0 reversed the original rule) | — | `tests/test_doctor.py::test_a_plain_text_source_type_is_reported_at_zero` |
| A partial share within a source type is **not** a warning | — | `tests/test_doctor.py::test_a_partial_share_within_a_source_type_is_not_a_warning` |
| The remedy distinguishes an unsupported source type from a headingless document | — | `tests/test_doctor.py::test_a_markdown_kb_with_no_headings_gets_the_other_remedy` |
| Heading coverage reflects the current index, not removed documents | — | `tests/test_doctor.py::test_a_removed_documents_chunks_stop_being_counted` |
| a KB with no hub edges reports `none`, cleanly | G6 | `tests/test_doctor.py::test_a_kb_with_no_edges_reports_none` |
| a `co-located` (`dir`) hub is named by its KB-root-relative path, not resolved through a lookup | G6 | `tests/test_doctor.py::test_a_directory_hub_is_named_by_its_kb_root_relative_path` |
| a degree tie between two **different** hub kinds breaks on `kind` before `key` — `nodes` is `UNIQUE (kind, key)`, so `key` alone is not a total order | G6 | `tests/test_doctor.py::test_a_cross_kind_tie_breaks_on_kind_before_key` |
| a degree tie breaks on `(kind, key)`, and the hubs it pushes out of the sample are still counted | G6 | `tests/test_doctor.py::test_a_degree_tie_breaks_deterministically_and_the_rest_are_counted` |
| a hub is named for a human — a document path, never a bare `nodes.id` | G6 | `tests/test_doctor.py::test_an_edge_hub_report_names_a_document_path_never_a_bare_node_id` |

## Release machinery

| What must be true | Increment | Where it is checked |
|---|---|---|
| the demo KB's eval numbers do not move | I3b | `make eval` against `tests/demo-kb/eval/baseline.json` (the committed file is the assertion) |
| the free-vs-paid delta is present and dated in DESIGN §9 | I9 | `tests/test_verification.py::test_the_measured_paid_delta_is_present_and_dated` |
| a fragment cannot be malformed or miscategorised | — | `tests/test_fragments.py::test_an_unknown_category_is_refused_by_name`, `check.sh` gate |
| two agents editing shared documents are told before they merge | — | `tests/test_shared_file_overlap.py::test_uncommitted_work_counts`, `check.sh` gate |
| a core-only wheel still installs and runs | I9 | CI `build` job smoke step |
| the shipped wheel carries `prices.toml` and `floors.toml` | I9 | CI `build` job smoke step |
| `docs/STATUS.md` line 3 names `pinakes.__version__`, in the exact `**Latest release: x.y.z**` shape | fix | `tests/test_status_header_gate.py::test_the_real_status_file_agrees_with_the_real_version`, `tests/test_status_header_gate.py::test_agreeing_versions_pass` |
| a drifted header fails naming both versions and the file | fix | `tests/test_status_header_gate.py::test_disagreeing_versions_fail_naming_both` |
| deleting, moving or reformatting the header cannot silence the gate | fix | `tests/test_status_header_gate.py::test_a_missing_line_fails`, `tests/test_status_header_gate.py::test_a_reformatted_line_fails`, `tests/test_status_header_gate.py::test_the_header_on_the_wrong_line_fails` |
| landing refuses when the default branch's sha did not move — the merge that reports success and lands nothing | fix | `tests/test_land.py::test_refuses_when_the_default_branch_did_not_move`, `tests/test_land.py::test_cleanup_does_not_run_when_the_landing_was_refused` |
| landing merges in the primary checkout even when invoked from the feature worktree | fix | `tests/test_land.py::test_merges_in_the_primary_checkout_even_when_invoked_from_the_feature_worktree` |
| landing cannot fold uncommitted work into the merge, or land onto the wrong branch | fix | `tests/test_land.py::test_refuses_a_dirty_primary_checkout`, `tests/test_land.py::test_refuses_to_merge_the_default_branch_into_itself` |
| `--cleanup` removes the worktree and **both** copies of the branch | fix | `tests/test_land.py::test_cleanup_removes_the_worktree_and_both_copies_of_the_branch` |
| `--cleanup-only` destroys nothing unless the branch is an ancestor of `origin/main` — "looks merged" is not "landed" | fix | `tests/test_land.py::test_cleanup_only_refuses_a_branch_whose_content_never_landed`, `tests/test_land.py::test_cleanup_only_removes_a_branch_that_landed_earlier` |
| the status-header gate is invoked, and can still fail | fix | `tests/test_check_script.py::test_check_sh_declares_the_status_header_gate`, `tests/test_check_script.py::test_ci_runs_the_status_header_gate_and_proves_it_can_fail` |
| the seven ordered release sequences in `CHANGELOG.md`, `docs/ROADMAP.md` and `docs/STATUS.md` read in release order | fix | `tests/test_release_order_gate.py::test_the_real_documents_are_in_release_order`, `tests/test_release_order_gate.py::test_an_ordered_tree_passes` |
| a row in the wrong position fails, naming the pair — each sequence checked in its own declared direction | fix | `tests/test_release_order_gate.py::test_a_row_out_of_order_is_named_with_its_neighbour`, `tests/test_release_order_gate.py::test_a_descending_sequence_is_checked_in_its_own_direction` |
| a pattern that stops matching fails rather than passing over a document it can no longer read | fix | `tests/test_release_order_gate.py::test_a_pattern_that_stops_matching_fails_rather_than_passing`, `tests/test_release_order_gate.py::test_every_pattern_still_matches_the_real_documents` |
| a sweep that updates one of the three documents and not another is caught | fix | `tests/test_release_order_gate.py::test_a_sweep_that_updates_one_document_and_not_another_is_caught` |
| a document the gate cannot read fails as a gate, never as a traceback | fix | `tests/test_release_order_gate.py::test_a_document_the_gate_cannot_read_fails_as_a_gate` |
| STATUS's *Published on PyPI* prose is one of the checked sequences — `docs/RELEASING.md` named it as a place a release stales and delegated its placement to this gate, which could not read it | fix | `tests/test_release_order_gate.py::test_a_prose_entry_out_of_order_is_named_with_its_neighbour`, `tests/test_release_order_gate.py::test_every_pattern_still_matches_the_real_documents` |
| that list may lag the release sequences — an entry is held back until it is verified from the index — but may never lead them | fix | `tests/test_release_order_gate.py::test_the_prose_list_may_lag_the_release_sequences`, `tests/test_release_order_gate.py::test_the_prose_list_may_not_lead_the_release_sequences` |
| a sequence that began later carries its own floor, and the pattern matches only its own entries | fix | `tests/test_release_order_gate.py::test_a_sequence_carries_its_own_floor`, `tests/test_release_order_gate.py::test_the_prose_pattern_does_not_match_the_roadmap_table` |
| a fragment opening with a `---` front-matter fence is refused before `--apply` can splice it into the document verbatim, while a horizontal rule inside a body is left alone | fix | `tests/test_fragments.py::test_a_fragment_that_opens_with_front_matter_is_refused`, `tests/test_fragments.py::test_a_horizontal_rule_inside_a_body_is_left_alone`, `tests/test_fragments.py::test_front_matter_is_refused_before_apply_can_splice_it` |
| every per-release section in `docs/ROADMAP.md` sits under the Part whose declared range holds its version — a shipped release filed under *What is not built* leaves every sequence sorted | fix | `tests/test_release_order_gate.py::test_a_section_under_a_rangeless_part_fails_while_every_sequence_stays_sorted`, `tests/test_release_order_gate.py::test_a_section_one_part_early_is_caught_and_names_both_parts`, `tests/test_release_order_gate.py::test_the_real_document_places_every_section_under_its_part` |
| a Part heading whose range stops parsing holds nothing rather than everything, and the three range forms are each read | fix | `tests/test_release_order_gate.py::test_a_part_whose_range_stops_parsing_holds_nothing_rather_than_everything`, `tests/test_release_order_gate.py::test_the_prefix_range_form_is_actually_read`, `tests/test_release_order_gate.py::test_a_part_pattern_that_stops_matching_fails_rather_than_passing` |
| every release at or after a sequence's declared start appears in it — a deleted row leaves every surviving pair sorted, so no ordering check sees it | fix | `tests/test_release_order_gate.py::test_a_release_missing_from_the_middle_is_caught`, `tests/test_release_order_gate.py::test_the_real_documents_are_complete_from_their_declared_starts` |
| the start is declared, never derived — deleting a sequence's *oldest* row would move a derived start and hide the deletion | fix | `tests/test_release_order_gate.py::test_a_deleted_first_row_is_caught_because_the_start_is_declared`, `tests/test_release_order_gate.py::test_a_release_before_a_sequences_declared_start_is_not_required` |
| a lagging sequence may be short at the top and may not have a hole underneath | fix | `tests/test_release_order_gate.py::test_a_lagging_sequence_need_not_have_reached_the_newest_release`, `tests/test_release_order_gate.py::test_a_lagging_sequence_may_not_have_a_hole_below_its_own_newest` |
| a sequence permitted to lag may be at most `MAX_VERIFICATION_LAG` releases behind, and the failure names both causes without choosing — the documents cannot tell a deleted entry from an unwritten one | fix | `tests/test_release_order_gate.py::test_a_lag_past_the_declared_bound_fails_and_names_both_causes`, `tests/test_release_order_gate.py::test_a_lag_within_the_declared_bound_stays_green`, `tests/test_release_order_gate.py::test_the_lag_bound_does_not_apply_to_a_sequence_that_may_not_lag` |
| STATUS's **Published versions** row is a seventh sequence, distinct from the *Published on PyPI* prose forty lines above it in the same file — the row had fallen four releases behind while the gate reported those releases present, in the sequence next door | fix | `tests/test_release_order_gate.py::test_the_row_and_the_prose_are_two_sequences_not_one`, `tests/test_release_order_gate.py::test_a_release_missing_from_the_row_is_named_even_though_the_prose_has_it`, `tests/test_release_order_gate.py::test_the_row_drifting_behind_the_prose_beside_it_is_caught` |
| a sequence living inside one line is scoped by a `within` anchor, so the ~20 version numbers in that cell's trailing prose are not read into it, and a renamed row matches nothing rather than passing vacuously | fix | `tests/test_release_order_gate.py::test_the_prose_beside_the_row_is_not_read_as_part_of_it`, `tests/test_release_order_gate.py::test_a_renamed_row_matches_nothing_rather_than_passing_vacuously` |
| a `within` anchor that matches twice is refused rather than read first — taking one of several regions would splice two lists into a sequence sorted by accident — and an anchor whose group count is wrong fails when the module is built | fix | `tests/test_release_order_gate.py::test_a_second_row_is_refused_rather_than_read_first`, `tests/test_release_order_gate.py::test_a_within_anchor_with_the_wrong_number_of_groups_is_refused_at_import` |
| a sequence may declare it must not fall behind another recording the same event — the **Published versions** row may lag the release documents but never the *Published on PyPI* prose beside it, which is where both recorded drifts began while the lag bound stayed silent | fix | `tests/test_release_order_gate.py::test_the_row_may_not_lag_the_prose_recording_the_same_verification`, `tests/test_release_order_gate.py::test_the_row_drifting_behind_the_prose_beside_it_is_caught` |
| and that rule does not fire when both lists are legitimately a release behind the release documents, which is the ordinary state between cutting a release and verifying it on the index | fix | `tests/test_release_order_gate.py::test_the_row_may_still_lag_the_release_documents_alongside_the_prose` |
| a `not_behind` naming a sequence that does not exist is refused when the module is built — the validator is fed a **bad** sequence, not only the constants it already validates | fix | `tests/test_release_order_gate.py::test_a_not_behind_naming_no_sequence_is_refused_when_the_module_is_built` |
| two Parts may not claim the same versions, and the Parts ascend with the document — appending a range to the rangeless final Part would otherwise legitimise a section filed under it | fix | `tests/test_release_order_gate.py::test_a_range_appended_to_a_rangeless_part_cannot_silence_placement`, `tests/test_release_order_gate.py::test_parts_must_ascend_with_the_document` |
| the Part floor is the real count, so demoting the last `# Part` heading fails instead of re-attributing its sections to the Part above | fix | `tests/test_release_order_gate.py::test_demoting_the_last_part_heading_fails_the_floor`, `tests/test_release_order_gate.py::test_a_part_pattern_that_stops_matching_fails_rather_than_passing` |
| the release-order gate is invoked, and can still fail | fix | `tests/test_check_script.py::test_check_sh_declares_the_release_order_gate`, `tests/test_check_script.py::test_ci_runs_the_release_order_gate_and_proves_it_can_fail` |
| the mutation harness refuses a target that is untracked or gitignored, or that differs from `HEAD` — before any file is written. `git status` prints nothing for an ignored file, so cleanliness alone passed one with no `HEAD` version, for which the `git checkout --` it promises cannot work | — | `tests/test_mutate.py::test_a_target_that_differs_from_head_is_refused_before_the_first_write`, `tests/test_mutate.py::test_a_gitignored_target_is_refused_because_git_checkout_could_not_recover_it` |
| an anchor that does not occur **exactly once** is refused for the whole battery before the first mutation runs — a `str.replace` matching nothing reads as SURVIVED, and checking only at write time mutates every earlier mutant first | — | `tests/test_mutate.py::test_an_anchor_that_matches_nothing_refuses_before_writing_anything`, `tests/test_mutate.py::test_an_anchor_that_matches_twice_refuses_rather_than_choosing`, `tests/test_mutate.py::test_a_stale_anchor_in_the_last_mutant_refuses_before_the_first_one_runs`, `tests/test_mutate.py::test_applied_refuses_a_bad_anchor_even_though_the_pre_flight_already_checked` |
| the target comes back byte-identical — after a normal run, after a body that raised, and after `SIGTERM`, `SIGHUP` or `SIGQUIT`, whose default disposition skips `finally` — and a restore that did not take is caught rather than trusted | — | `tests/test_mutate.py::test_the_target_is_restored_byte_for_byte_after_a_run`, `tests/test_mutate.py::test_a_body_that_raises_still_restores`, `tests/test_mutate.py::test_the_target_is_restored_when_the_run_is_killed_mid_flight`, `tests/test_mutate.py::test_a_restore_that_did_not_take_is_caught_rather_than_trusted`, `tests/test_mutate.py::test_a_restore_that_git_still_sees_voids_the_whole_report` |
| `__pycache__` is cleared after the write **and** after the restore, so a same-length mutant is never read off stale bytecode (T3) — with the control that forges the condition and proves the trap is real | — | `tests/test_mutate.py::test_the_bytecode_cache_is_cleared_after_the_write_and_after_the_restore`, `tests/test_mutate.py::test_a_stale_pyc_really_does_report_a_same_length_mutant_as_survived`, `tests/test_mutate.py::test_a_same_length_mutant_is_killed_end_to_end`, `tests/test_mutate.py::test_a_relocated_bytecode_cache_is_refused_rather_than_guessed_at` |
| pytest never sees `-x` — refused in the battery's command, refused in a selector, and dropped from the environment, where `PYTEST_ADDOPTS` would otherwise narrow a two-test kill to one | — | `tests/test_mutate.py::test_a_battery_that_asks_for_x_in_its_pytest_command_is_refused`, `tests/test_mutate.py::test_a_selector_that_smuggles_x_in_is_refused_too`, `tests/test_mutate.py::test_pytest_addopts_in_the_environment_cannot_narrow_the_run` |
| a **collection** error is the invalid mutant and never a kill (T4); a **setup or teardown** error is neither a kill nor a survival; and a real failure beside one is still a kill | — | `tests/test_mutate.py::test_an_invalid_mutant_is_its_own_outcome_never_killed_and_never_survived`, `tests/test_mutate.py::test_a_setup_error_beside_a_real_failure_is_still_a_kill`, `tests/test_mutate.py::test_a_setup_error_with_no_failure_beside_it_is_not_a_kill`, `tests/test_mutate.py::test_a_teardown_error_is_not_a_kill_either`, `tests/test_mutate.py::test_a_setup_error_is_errored_even_if_the_run_somehow_exited_zero` |
| a selector that skips, is already red, collects nothing or pytest rejects is refused **before any file is touched** — each of them otherwise reports a confident, wrong outcome for every mutant aimed at it | — | `tests/test_mutate.py::test_a_selector_whose_tests_all_skip_is_refused_before_anything_is_written`, `tests/test_mutate.py::test_a_selector_that_is_already_red_is_refused_rather_than_killing_every_mutant`, `tests/test_mutate.py::test_a_selector_that_collects_nothing_is_refused`, `tests/test_mutate.py::test_a_selector_pytest_rejects_is_refused_naming_it` |
| a batch where **nothing died** exits non-zero as a broken harness, and only `--allow-zero-kills` accepts it; a mutant that never terminates or that makes every test skip is ERRORED rather than a survivor | — | `tests/test_mutate.py::test_a_batch_with_no_kills_exits_non_zero_as_a_broken_harness`, `tests/test_mutate.py::test_allow_zero_kills_accepts_the_same_batch`, `tests/test_mutate.py::test_a_mutant_that_never_terminates_is_errored_rather_than_hanging_the_battery`, `tests/test_mutate.py::test_a_mutant_that_makes_every_test_skip_is_not_a_survivor`, `tests/test_mutate.py::test_a_timed_out_run_is_errored_even_if_it_somehow_reported_passing_tests` |
| a killed row names the tests that killed it, the assertion that fired and how many of the selector ran — and the pasteable summary never names a killer on a row it labels ERRORED | — | `tests/test_mutate.py::test_a_mutant_the_tests_catch_is_killed_and_names_the_test_that_caught_it`, `tests/test_mutate.py::test_the_baseline_reports_how_many_tests_it_ran`, `tests/test_mutate.py::test_an_indentation_only_mutant_is_not_rendered_as_a_no_op`, `tests/test_mutate.py::test_the_table_withholds_a_killer_even_when_an_errored_row_has_failures` |
| mutating a **test file** is refused, mutating outside the repository is refused, and every malformed battery or `--repo` is a refusal with a remedy rather than a traceback | — | `tests/test_mutate.py::test_a_test_file_target_is_refused_because_mutating_a_test_stays_manual`, `tests/test_mutate.py::test_a_target_outside_the_repository_is_refused`, `tests/test_mutate.py::test_a_malformed_battery_is_a_refusal_not_a_traceback`, `tests/test_mutate.py::test_a_repo_that_does_not_exist_is_a_refusal_not_a_traceback`, `tests/test_mutate.py::test_a_directory_that_is_not_a_git_working_tree_is_refused`, `tests/test_mutate.py::test_repo_selects_the_working_tree_to_mutate` |
| `--check-anchors` resolves every anchor against the **working tree** — not `HEAD`, so it still answers mid-refactor — reports **every** failure rather than the first, and says on success which two rots it cannot see. A run refuses that same uncommitted tree, which is what makes the difference real | — | `tests/test_mutate.py::test_check_anchors_resolves_every_anchor_and_runs_nothing`, `tests/test_mutate.py::test_check_anchors_reads_the_working_tree_rather_than_head`, `tests/test_mutate.py::test_check_anchors_reports_every_stale_anchor_not_only_the_first`, `tests/test_mutate.py::test_check_anchors_says_what_a_green_check_does_not_prove`, `tests/test_mutate.py::test_a_battery_check_anchors_passes_is_one_a_run_does_not_refuse` |
| one file belongs to one battery, and a run takes one battery — a second battery's kills counted into the first's would let `--allow-zero-kills` excuse a batch that never needed it | — | `tests/test_mutate.py::test_check_anchors_refuses_a_file_claimed_by_two_batteries`, `tests/test_mutate.py::test_two_batteries_claiming_different_files_are_accepted`, `tests/test_mutate.py::test_running_more_than_one_battery_at_a_time_is_refused` |
| a stale anchor, a deleted target, a renamed test and a second battery claiming a file each turn `./check.sh` red — the committed batteries are read by something, which is the only thing that stops `tools/batteries/` becoming a directory of files nobody resolves. With the non-empty control, since every one of those iterates a glob | — | `tests/test_batteries.py::test_every_anchor_still_resolves_exactly_once_in_the_file_it_names`, `tests/test_batteries.py::test_every_kills_selector_resolves_to_a_test_that_exists`, `tests/test_batteries.py::test_no_file_is_claimed_by_two_batteries`, `tests/test_batteries.py::test_every_battery_is_named_for_a_file_it_actually_mutates`, `tests/test_batteries.py::test_the_directory_is_not_empty_and_every_battery_carries_mutants`, `tests/test_batteries.py::test_every_mutant_names_the_four_keys_mutate_needs`, `tests/test_batteries.py::test_a_committed_battery_omits_pytest_and_takes_the_default` |

| What must be true | Increment | Where it is checked |
|---|---|---|
| every relative link and heading anchor resolves in the Markdown `mkdocs build --strict` never sees — `CLAUDE.md`, the root `README.md`, `CHANGELOG.md`, `plans/`, the fragment READMEs and `docs/README.md`, which held eleven broken links before the gate | fix | `tests/test_markdown_link_gate.py::test_a_link_to_a_file_that_does_not_exist_is_reported`, `tests/test_markdown_link_gate.py::test_a_link_to_a_heading_that_does_not_exist_is_reported`, `tests/test_markdown_link_gate.py::test_a_link_that_resolves_above_the_repository_root_is_reported` |
| a **quoted** link — inside a code span or a fenced block — is never resolved, so a document quoting another document's links is never asked to corrupt the quotation to satisfy the gate | fix | `tests/test_markdown_link_gate.py::test_a_quoted_link_inside_a_code_span_is_not_resolved`, `tests/test_markdown_link_gate.py::test_a_link_inside_a_fenced_block_is_not_resolved` |
| the gate and the published site slugify **every heading in the repository** identically, so the duplicated GitHub algorithm cannot drift from `mkdocs_hooks.py` | fix | `tests/test_markdown_link_gate.py::test_the_gate_and_the_site_slugify_every_heading_in_the_repository_identically`, `tests/test_markdown_link_gate.py::test_the_em_dash_rule_that_the_site_hook_exists_for_is_honoured` |
| a link whose **case** does not match the filesystem is caught on the case-insensitive machine that wrote it, rather than on the ubuntu runner that publishes it | fix | `tests/test_markdown_link_gate.py::test_a_link_whose_case_does_not_match_the_filesystem_is_reported` |
| link syntax the parser cannot read **fails rather than being skipped**, and link text wrapped across lines is still parsed — a checker that quietly matches less than it should reports a pass it never earned | fix | `tests/test_markdown_link_gate.py::test_link_syntax_the_parser_cannot_read_is_reported_rather_than_skipped`, `tests/test_markdown_link_gate.py::test_link_text_wrapped_across_lines_is_still_parsed` |
| a **directory** link resolves, because GitHub renders it as a listing — the false-positive class an `is_file()` resolver invents and a `docs/`-only control never exercises | fix | `tests/test_markdown_link_gate.py::test_a_link_to_a_directory_is_accepted`, `tests/test_markdown_link_gate.py::test_a_trailing_slash_directory_that_does_not_exist_is_still_reported` |
| the scope is read from `mkdocs.yml` rather than assumed, covers the `README.md` the site excludes, and a missing `docs_dir` is refused rather than defaulted to nothing | fix | `tests/test_markdown_link_gate.py::test_the_scope_is_read_from_mkdocs_yml_and_covers_the_readme_the_site_excludes`, `tests/test_markdown_link_gate.py::test_a_missing_docs_dir_in_mkdocs_yml_is_refused_rather_than_defaulted` |
| the real `docs/` corpus is clean, which is this checker's only control — the expected answer there is supplied by `mkdocs build --strict`, independently of the checker | fix | `tests/test_markdown_link_gate.py::test_the_real_docs_directory_is_clean_which_is_this_checkers_only_control` |
| the regex extractor finds every link a **real Markdown renderer** emits and invents none — measured over all 114 tracked files and 894 rendered links, which is what licenses the gate staying stdlib-only instead of taking the docs toolchain as a dependency | fix | `tests/test_markdown_link_gate.py::test_the_extractor_agrees_with_a_real_renderer_on_every_file_in_the_repository` |
| the gate survives the window every release passes through — `fragments.py --apply` splices and deletes each fragment while `check.sh` runs before the `git add`, so a tracked file is absent from disk — and refuses a non-work-tree or a missing `--paths` entry with a message rather than a traceback | fix | `tests/test_markdown_link_gate.py::test_a_tracked_file_deleted_mid_release_is_skipped_rather_than_crashing`, `tests/test_markdown_link_gate.py::test_a_directory_that_is_not_a_work_tree_is_refused_with_a_message`, `tests/test_markdown_link_gate.py::test_paths_naming_a_file_that_does_not_exist_is_refused_rather_than_traced` |
| the markdown-link gate is invoked, and can still fail | fix | `tests/test_check_script.py::test_check_sh_declares_the_markdown_link_gate`, `tests/test_check_script.py::test_ci_runs_the_markdown_link_gate_and_proves_it_can_fail` |

## The source walk stays inside the KB (0.7.1)

Three defects live since before 0.5.0 let `[sources] include` mint sidecars **outside** the KB —
against the `docs/` belongs to the user invariant. A fourth was found by a test written to pin
*correct* behaviour. The rows below were added on 20260804: 0.7.1 shipped seventeen tests and
touched this file not at all, which `tests/test_verification.py` cannot detect — it walks from this
document to the tests, proving no row is fiction, and structurally cannot prove no guarantee is
un-rowed.

| What must be true | Increment | Where it is checked |
|---|---|---|
| an `include` pattern that climbs out of the KB is refused at load | 0.7.1 | `tests/test_sync.py::test_an_include_pattern_that_climbs_out_of_the_kb_is_refused_at_load` |
| an absolute `include` pattern is a named `ManifestError`, never a traceback | 0.7.1 | `tests/test_sync.py::test_an_absolute_include_pattern_is_a_manifest_error_not_a_traceback` |
| a symlinked directory cannot carry the walk out of the KB | 0.7.1 | `tests/test_sync.py::test_a_symlinked_directory_cannot_carry_the_walk_out_of_the_kb` |
| a symlinked document *inside* the KB is still ingested — containment is not a ban on symlinks | 0.7.1 | `tests/test_sync.py::test_a_symlinked_document_inside_the_kb_is_still_ingested` |
| a `..` pattern that stays inside the KB is legal, and one file reached two legal ways is one document | 0.7.1 | `tests/test_sync.py::test_a_dot_dot_pattern_that_stays_inside_the_kb_is_accepted`, `tests/test_sync.py::test_one_file_reached_by_two_legal_spellings_is_one_document`, `tests/test_sync.py::test_the_same_document_is_ingested_by_a_fixed_and_a_globbed_pattern_alike` |
| a leading glob, or a `**` before the `..`, does not defeat the static refusal | 0.7.1 | `tests/test_sync.py::test_a_leading_glob_does_not_defeat_the_static_refusal`, `tests/test_sync.py::test_a_double_star_before_a_dot_dot_does_not_defeat_the_refusal` |
| an escaping pattern is refused **without enumerating the tree**, and a symlinked escape stops the walk rather than walking it | 0.7.1 | `tests/test_sync.py::test_an_escaping_pattern_is_refused_without_enumerating_the_tree`, `tests/test_sync.py::test_a_symlinked_escape_stops_the_walk_rather_than_enumerating_the_tree` |
| an escaping pattern matching only a directory is still caught | 0.7.1 | `tests/test_sync.py::test_an_escaping_pattern_that_matches_only_a_directory_is_still_caught` |
| the escape is reported once per pattern, never once per file | 0.7.1 | `tests/test_sync.py::test_the_escape_is_reported_once_per_pattern_not_once_per_file` |
| an escape under one root does not drop documents under another | 0.7.1 | `tests/test_sync.py::test_an_escape_under_one_root_does_not_drop_documents_under_another` |
| an `exclude` pattern may contain `..`, and a root that does not exist yet still loads | 0.7.1 | `tests/test_sync.py::test_an_excluded_pattern_may_contain_dot_dot`, `tests/test_sync.py::test_a_root_that_does_not_exist_yet_still_loads` |
| the density gate survives a root reached through a symlinked parent | 0.7.1 | `tests/test_partner_kb.py::test_the_gate_survives_a_root_reached_through_a_symlinked_parent` |

## The template version archive and its drift gate (T1)

The rows this increment's own tests require, and no others. A version number that cannot be
compared to anything is the promise `pnk doctor` made for eleven releases without being able to
keep it — so what is pinned here is mostly *which leg reported*, not merely that the gate failed.

| What must be true | Increment | Where it is checked |
|---|---|---|
| the live template matches the version it declares | T1 | `tests/test_template_drift.py::test_the_live_template_matches_its_own_archived_version` |
| editing a consumed file without bumping the version fails the gate | T1 | `tests/test_template_drift.py::test_editing_a_consumed_file_without_bumping_the_version_fails_the_gate` |
| a comment-only edit fails it too — comments are the product (D-3 option A) | T1 | `tests/test_template_drift.py::test_editing_only_a_comment_fails_the_gate` |
| the template's `README.md` is in scope, correcting `docs/KB-UPDATES.md` §6 | T1 | `tests/test_template_drift.py::test_editing_the_template_readme_fails_the_gate` |
| a template that gains a consumed file is covered without editing the gate | T1 | `tests/test_template_drift.py::test_a_new_consumed_file_is_covered_without_editing_the_gate` |
| the archive is outside the live content hash, so archiving N does not change N+1 | T1 | `tests/test_template_drift.py::test_the_archive_itself_is_outside_the_hash` |
| a bumped version with no archived directory fails | T1 | `tests/test_template_drift.py::test_a_bumped_version_with_no_archived_directory_fails` |
| a version bumped with no content change fails — reachable only because `template.toml` is outside the hash | T1 | `tests/test_template_drift.py::test_a_version_bump_with_no_content_change_fails_the_gate`, `tests/test_template_drift.py::test_the_declaration_is_outside_the_content_hash` |
| an archived version edited in one file fails against the ledger | T1 | `tests/test_template_drift.py::test_a_modified_archived_version_fails_against_the_ledger` |
| tampering with the *live* version's archive reports the ledger, not the live comparison — the two have opposite remedies | T1 | `tests/test_template_drift.py::test_editing_the_live_versions_archive_is_reported_as_a_ledger_failure` |
| a ledger row with no archived directory fails | T1 | `tests/test_template_drift.py::test_a_ledger_row_with_no_archived_directory_fails` |
| an archived version that no longer renders fails, naming the version and the variable | T1 | `tests/test_template_drift.py::test_an_archived_version_that_no_longer_renders_fails_the_gate` |
| a three-file edit that passes every content leg is caught by history, before it merges | T1 | `tests/test_template_drift.py::test_a_three_file_edit_is_caught_by_the_history_leg` |
| and once both commits have landed, when the content comparison can no longer see it | T1 | `tests/test_template_drift.py::test_an_archive_edited_after_it_shipped_is_caught_once_both_commits_have_landed` |
| adding an archive and correcting it before landing is not an edit — the sequence `docs/BUILDING.md` requires | T1 | `tests/test_template_drift.py::test_adding_an_archive_then_correcting_it_before_landing_is_not_an_edit` |
| with no published branch the leg skips rather than guessing | T1 | `tests/test_template_drift.py::test_the_history_leg_skips_when_there_is_no_published_branch` |
| a relative `--templates` cannot make the leg claim it ran over a tree it never looked at | T1 | `tests/test_template_drift.py::test_a_relative_templates_path_does_not_let_the_history_leg_claim_it_ran` |
| without git history the gate says so, and the skip is a real loss of coverage — not a formality | T1 | `tests/test_template_drift.py::test_the_gate_names_its_reason_when_it_cannot_run`, `tests/test_template_drift.py::test_a_shallow_clone_skips_the_history_leg_rather_than_passing_it` |
| an archive not yet committed is new, not frozen | T1 | `tests/test_template_drift.py::test_an_uncommitted_archive_is_not_an_edit` |
| the gate is actually invoked — by `check.sh`, and by its own CI job with full history | T1 | `tests/test_template_drift.py::test_the_gate_is_invoked_by_check_sh`, `tests/test_template_drift.py::test_the_gate_has_its_own_ci_job_with_full_history` |
| a file git ignores is not part of the template, and one it does not ignore still is | T1 | `tests/test_template_drift.py::test_a_file_git_ignores_is_not_part_of_the_template`, `tests/test_template_drift.py::test_an_untracked_file_git_does_not_ignore_is_still_part_of_the_template` |
| the hash is unchanged where git cannot answer — an sdist or a vendored copy | T1 | `tests/test_template_drift.py::test_the_hash_is_the_same_where_git_cannot_answer` |
| an archived version carries its own `template.toml`, declaring the version its directory is named for | T1 | `tests/test_template_drift.py::test_an_archived_version_without_its_declaration_fails`, `tests/test_template_drift.py::test_an_archived_version_declaring_a_different_version_fails` |
| the gate names which history mode it ran in, every time | T1 | `tests/test_template_drift.py::test_the_gate_says_which_history_mode_it_ran_in` |
| leg (ii) stopped being vacuous when E4 archived `notes@1.2` — the gate said so while it had one version to compare, and the assertion is now that the caveat is **gone**, which is the only thing that keeps it trustworthy the next time it appears | T1 | `tests/test_template_drift.py::test_leg_two_stopped_being_vacuous_when_the_second_version_was_archived` |
| a template name with a path separator or `..` is refused with a message, not a traceback | T1 | `tests/test_template_drift.py::test_a_template_name_with_a_path_separator_or_dotdot_is_refused`, `tests/test_template_drift.py::test_a_valid_template_name_still_resolves` |
| an archived *version* with a path separator is refused too — it arrives from a KB's own manifest | T1 | `tests/test_template_drift.py::test_an_archived_version_with_a_path_separator_is_refused` |
| `1.0` is never archived (D-2b), and `archived_versions` orders by version, not by string — **asserted against the function itself**, since the row's original test exercised `version_key` and never called it. A template with no archive gets an empty list rather than a `FileNotFoundError`, and a stray file beside the versions is not one | T1 | `tests/test_template_drift.py::test_archived_versions_lists_exactly_what_is_archived`, `tests/test_template_drift.py::test_archived_versions_sorts_by_version_not_by_string`, `tests/test_template_drift.py::test_archived_versions_orders_by_version_and_not_by_string` |
| a template with no archive at all, and a stray file beside the archived versions | T1 | `tests/test_template_drift.py::test_archived_versions_is_empty_rather_than_raising_when_there_is_no_archive` |
| `render_archived` renders an archived manifest, and names the version when it is not archived | T1 | `tests/test_template_drift.py::test_render_archived_renders_the_archived_manifest`, `tests/test_template_drift.py::test_render_archived_refuses_a_version_that_is_not_archived` |
| the content hash covers a file's path as well as its bytes | T1 | `tests/test_template_drift.py::test_the_hash_covers_the_path_as_well_as_the_bytes` |

## `pnk upgrade` — the report, its placement predicate and its exit codes (T3)

Every positive row runs against a **synthetic two-version template**, because D-2b leaves the
shipped `notes` with one archived version and so with exactly one reachable outcome. The one row
that runs against `notes` says so.

| What must be true | Increment | Where it is checked |
|---|---|---|
| the diff is `base → ours`, so a user's own edit appears in no changed line — on both surfaces | T3 | `tests/test_cli_upgrade.py::test_the_report_never_diffs_the_user_against_the_template`, `tests/test_cli_upgrade.py::test_a_user_edit_the_template_never_touched_appears_nowhere_in_the_output` |
| a changed value is shown **old and new**, never only the value being moved to | T3 | `tests/test_cli_upgrade.py::test_a_drifted_kb_prints_the_template_diff` |
| a hunk already present in the manifest is *already applied* — not clean, not conflict | T3 | `tests/test_cli_upgrade.py::test_a_hunk_already_present_in_theirs_is_reported_as_already_applied` |
| ...and the **order** of the predicate is what makes that true for a pure addition | T3 | `tests/test_cli_upgrade.py::test_a_pure_addition_already_present_is_already_applied_not_clean` |
| a user-edited region is a conflict, while the untouched hunk still places | T3 | `tests/test_cli_upgrade.py::test_a_user_edited_region_is_reported_as_a_conflict_not_applied` |
| reordering inside a hunk's own window is a conflict, not a silent success | T3 | `tests/test_cli_upgrade.py::test_a_reordered_manifest_is_a_conflict_not_a_silent_success` |
| the conflict explanation is printed **only** when there is a conflict, and the summary names only the outcomes that occurred | T3 | `tests/test_cli_upgrade.py::test_a_report_with_no_conflict_does_not_explain_conflicts` |
| a context matching twice is a conflict — uniqueness is part of the predicate | T3 | `tests/test_cli_upgrade.py::test_a_hunk_whose_context_matches_twice_is_a_conflict` |
| ...on **both** of its branches, not only the clean one — a gap mutation testing found and reading had not | T3 | `tests/test_cli_upgrade.py::test_an_already_applied_hunk_matching_twice_is_a_conflict_too` |
| a calibrated KB, which has uncommented `[retrieval.confidence]`, conflicts on that region | T3 | `tests/test_cli_upgrade.py::test_a_kb_with_an_uncommented_retrieval_confidence_table_conflicts_on_that_region` |
| `[[links.kb]]` entries and tables the template never stamped do **not** stop a hunk placing | T3 | `tests/test_cli_upgrade.py::test_a_kb_with_links_kb_entries_still_places_unambiguous_hunks`, `tests/test_cli_upgrade.py::test_a_manifest_with_extra_tables_still_places_unambiguous_hunks` |
| nothing under the KB is written — the path set, the bytes **and** `st_mtime_ns`, over files and directories alike. Bytes and paths alone let this increment's own named mutation survive | T3 | `tests/test_cli_upgrade.py::test_nothing_under_the_kb_is_written`, `tests/test_cli_upgrade.py::test_a_current_kb_prints_up_to_date_and_writes_nothing` |
| `--json` reports the same hunks, in the same order, as the human output | T3 | `tests/test_cli_upgrade.py::test_json_and_human_output_report_the_same_hunks` |
| ...and is still JSON on the path that makes no comparison | T3 | `tests/test_cli_upgrade.py::test_the_json_refusal_is_still_json` |
| a version bump that leaves the manifest alone says so, rather than printing an empty diff | T3 | `tests/test_cli_upgrade.py::test_a_version_bump_with_no_manifest_change_says_same_manifest` |
| **`3` means *no baseline* and nothing else** — every other outcome's code is asserted beside it (O-2) | T3 | `tests/test_cli_upgrade.py::test_cannot_compare_exits_three_and_nothing_else_does` |
| a genuine operational failure still exits `1` (O-2) | T3 | `tests/test_cli_upgrade.py::test_an_operational_failure_still_exits_one` |
| the *no baseline* causes are reported rather than raised: an unarchived version, a template not installed, a KB recording none, and an archive this build cannot render. **`docs/CLI.md` lists five because it splits *recorded* from *installed*; those two are one branch and one test** — and an unarchived installed version is unreachable for a shipped template, since T1's gate leg (v) refuses a live version that is not archived | T3 | `tests/test_cli_upgrade.py::test_an_unarchived_recorded_version_refuses_with_a_remedy`, `tests/test_cli_upgrade.py::test_a_template_not_installed_here_cannot_compare`, `tests/test_cli_upgrade.py::test_a_kb_recording_no_template_cannot_compare`, `tests/test_cli_upgrade.py::test_an_archived_version_this_build_cannot_render_cannot_compare` |
| a removed line the manifest **repeats** (a blank line, a bare `#`) does not block *already applied* | T3 | `tests/test_cli_upgrade.py::test_a_removed_line_the_manifest_repeats_does_not_block_already_applied` |
| ...and a deletion **not yet** applied is still *clean* — the control for the clause above | T3 | `tests/test_cli_upgrade.py::test_a_deletion_not_yet_applied_is_clean_not_already_applied` |
| the printed diff is a real unified diff, `@@` ranges included, checked against `difflib`'s own | T3 | `tests/test_cli_upgrade.py::test_the_printed_diff_is_a_real_unified_diff` |
| the listing names the table each hunk falls in — and an array element, an array-of-tables header and a header with a trailing comment are each judged correctly | T3 | `tests/test_cli_upgrade.py::test_the_listing_names_the_table_each_hunk_falls_in`, `tests/test_cli_upgrade.py::test_which_line_counts_as_the_table_a_hunk_falls_in` |
| **`pnk doctor` and `pnk upgrade` say the same thing about an unarchived version** — one wording, one home | T3 | `tests/test_cli_upgrade.py::test_doctor_and_upgrade_say_the_same_thing_about_an_unarchived_version` |
| the `cannot compare:` prefix opens **every** *no baseline* line, which `docs/CLI.md` publishes as a scriptable contract | T3 | asserted in all four: `tests/test_cli_upgrade.py::test_an_unarchived_recorded_version_refuses_with_a_remedy`, `tests/test_cli_upgrade.py::test_a_template_not_installed_here_cannot_compare`, `tests/test_cli_upgrade.py::test_a_kb_recording_no_template_cannot_compare`, `tests/test_cli_upgrade.py::test_an_archived_version_this_build_cannot_render_cannot_compare` |
| the remedy names the **oldest** archived version — "stamped from X or later" excludes nothing | T3 | `tests/test_cli_upgrade.py::test_an_unarchived_recorded_version_refuses_with_a_remedy`, `tests/test_template_drift.py::test_cannot_compare_reads_correctly_for_one_missing_version_and_for_two` |
| ...and its plural agreement, its `and`-join and its empty-archive fallback all read correctly | T3 | `tests/test_template_drift.py::test_cannot_compare_reads_correctly_for_one_missing_version_and_for_two` |
| a `code span` in a remedy is never broken across two lines, and one longer than the wrap runs over rather than being cut | T3 | `tests/test_cli_upgrade.py::test_a_code_span_is_never_broken_across_two_lines` |
| the `--json` payload is a wire contract: keys and string values written out, never derived from the enums that produce them | T3 | `tests/test_cli_upgrade.py::test_the_json_payload_is_a_wire_contract_written_out_in_full` |
| the one-line `--help` says the command writes nothing **without `--apply`** — the qualifier is T4's, and a flat *writes nothing* is now false | T3, T4 | `tests/test_cli_upgrade.py::test_the_help_line_says_the_command_writes_nothing_without_apply` |
| the **remedy paragraph** wraps for a terminal. A one-line headline is not wrapped — as no other `pnk` command's is — and one of them, the unrenderable-archive refusal, interpolates a jinja2 error and can run over | T3 | `tests/test_cli_upgrade.py::test_no_line_of_the_report_runs_past_the_wrap` |
| against the **shipped** template, the only reachable outcome is *cannot compare* — every KB in existence | T3 | `tests/test_cli_upgrade.py::test_the_shipped_template_reaches_the_cannot_compare_path` |

## `pnk upgrade --apply` — the writer, its refusals and D-10's consent path (T4)

| What must be true | Increment | Test |
|---|---|---|
| only the **cleanly applying** hunks are written — an *already applied* one is skipped, not re-inserted | T4 | `tests/test_cli_upgrade.py::test_apply_writes_only_the_cleanly_applying_hunks` |
| one conflicting hunk refuses the **whole** run: the manifest is byte-identical, the message names the region on one line, and no `pinakes.toml.orig` is left behind | T4 | `tests/test_cli_upgrade.py::test_apply_refuses_entirely_when_any_hunk_conflicts` |
| the backup holds the state **before** the write, and an existing one is never overwritten | T4 | `tests/test_cli_upgrade.py::test_apply_leaves_an_orig_and_refuses_to_overwrite_an_existing_one` |
| ...and the output says it is untracked, since `init`'s `.gitignore` covers `.pinakes/` only | T4 | `tests/test_cli_upgrade.py::test_apply_prints_that_the_orig_is_untracked` |
| a held sync lock refuses, naming the holder — and the check itself writes nothing under `.pinakes/`, because it reads the lock rather than claiming it | T4 | `tests/test_cli_upgrade.py::test_apply_refuses_while_the_sync_lock_is_held` |
| a write that produces an unloadable manifest is rolled back to the original bytes, leaving no backup | T4 | `tests/test_cli_upgrade.py::test_a_write_that_produces_an_unloadable_manifest_is_rolled_back` |
| `[kb] template` is rewritten **inside `[kb]` only**, preserving alignment and any trailing comment, and never appended when absent | T4 | `tests/test_cli_upgrade.py::test_the_template_key_is_rewritten_only_inside_the_kb_table`, `tests/test_cli_upgrade.py::test_restamp_refuses_rather_than_appending_a_key_it_cannot_find` |
| **D-10 B: a `[budget]` hunk applies like any other** — the cap moves | T4 | `tests/test_cli_upgrade.py::test_a_budget_hunk_is_applied_like_any_other_hunk` |
| a money change is printed with **both** values under a spending-cap heading, in the report **and** under `--apply` | T4 | `tests/test_cli_upgrade.py::test_a_budget_change_is_printed_with_both_values` |
| ...and the heading provably precedes the first byte written, asserted by line position | T4 | `tests/test_cli_upgrade.py::test_the_budget_heading_precedes_the_first_write` |
| ...and it is **absent** in all four cases where no money moves: no `[budget]` hunk, an already-applied one, a refused run, and a `[budget]` hunk that changes only comments. **Without these the three rows above are decorative** | T4 | `tests/test_cli_upgrade.py::test_no_budget_heading_when_no_hunk_touches_budget`, `tests/test_cli_upgrade.py::test_no_budget_heading_when_the_budget_hunk_is_already_applied`, `tests/test_cli_upgrade.py::test_no_budget_heading_when_the_run_refuses_on_a_conflict`, `tests/test_cli_upgrade.py::test_no_budget_heading_when_the_budget_hunk_changes_only_comments` |
| applied keys that invalidate the index are named, with `pnk sync --rebuild` | T4 | `tests/test_cli_upgrade.py::test_apply_names_the_rebuild_when_an_applied_hunk_changes_an_index_invalidating_key` |
| **D-11 A: `requires_pinakes` is never written**, even by a bump that does add a key | T4 | `tests/test_cli_upgrade.py::test_requires_pinakes_is_never_written` |
| ...it is *recommended* instead, naming the added key and suggesting no version floor | T4 | `tests/test_cli_upgrade.py::test_a_key_adding_hunk_prints_a_requires_pinakes_recommendation` |
| ...silent when no applied hunk adds a key — today the only case a real template reaches (F2) | T4 | `tests/test_cli_upgrade.py::test_no_recommendation_when_no_applied_hunk_adds_a_key` |
| ...and the operands are `base + applied` rather than `ours`, so a key carried only by a **skipped** hunk is not credited to this run | T4 | `tests/test_cli_upgrade.py::test_a_key_carried_only_by_a_skipped_hunk_is_not_recommended` |
| an existing `requires_pinakes` is left byte-identical | T4 | `tests/test_cli_upgrade.py::test_an_existing_requires_pinakes_is_left_byte_identical` |
| `docs/` and `.pinakes/` are untouched, and no sync runs | T4 | `tests/test_cli_upgrade.py::test_apply_writes_nothing_under_docs_or_pinakes_state`, `tests/test_cli_upgrade.py::test_apply_does_not_run_a_sync` |
| the comment the template added is present afterwards — the end-to-end case a key-level implementation fails | T4 | `tests/test_cli_upgrade.py::test_the_comment_the_template_added_is_present_after_apply` |
| a CRLF manifest keeps its line endings throughout, and a **mixed**-ending one is refused rather than repaired | T4 | `tests/test_cli_upgrade.py::test_a_crlf_manifest_keeps_its_line_endings`, `tests/test_cli_upgrade.py::test_a_manifest_with_mixed_line_endings_is_refused` |
| the same conflict exits `0` as a report and `1` under `--apply`; *cannot compare* stays `3` under `--apply` and writes nothing; an up-to-date KB writes nothing | T4 | `tests/test_cli_upgrade.py::test_a_conflict_is_zero_as_a_report_and_one_under_apply`, `tests/test_cli_upgrade.py::test_cannot_compare_under_apply_still_exits_three_and_writes_nothing`, `tests/test_cli_upgrade.py::test_up_to_date_under_apply_writes_nothing` |
| `--json --apply` emits **one** document, carrying the result — or the refusal, rather than a message on stderr | T4 | `tests/test_cli_upgrade.py::test_json_apply_emits_one_document_carrying_the_result`, `tests/test_cli_upgrade.py::test_json_apply_emits_the_refusal_as_json_rather_than_a_traceback` |
| a manifest carrying `\u2028`, `\u2029` or `\x85` is refused — the report splits lines with `str.splitlines()` and the writer with `split("\n")`, so those three make *which lines* an ambiguous question | T4 | `tests/test_cli_upgrade.py::test_a_manifest_with_a_unicode_line_separator_is_refused_rather_than_rewritten` |
| a symlinked `pinakes.toml` is written **through**, never replaced by a regular file | T4 | `tests/test_cli_upgrade.py::test_a_symlinked_manifest_is_written_through_not_replaced` |
| the manifest keeps its own permissions across the rename-atomic write | T4 | `tests/test_cli_upgrade.py::test_apply_keeps_the_manifests_own_permissions` |
| a dotted key is named in full, so a spending cap is not reported as its table | T4 | `tests/test_cli_upgrade.py::test_a_dotted_key_is_named_in_full_not_by_its_first_segment` |
| the rollback restores through the same rename-atomic write | T4 | **none** — behaviourally identical to a direct write except under a crash mid-restore, which no in-process test can stage. Recorded rather than claimed |
| a table header **inside** a hunk moves the section from there on, so keys of a newly added table are not attributed to the preceding one — which would announce them as spending caps | T4 | `tests/test_cli_upgrade.py::test_a_table_added_inside_a_hunk_moves_the_section_from_there_on` |
| two clean hunks whose regions overlap in the manifest are refused as a conflict, and two that do not touch are planned | T4 | `tests/test_cli_upgrade.py::test_splices_refuses_two_hunks_that_land_on_top_of_each_other` |
| a hunk that no longer places uniquely is refused rather than written at a guessed position | T4 | `tests/test_cli_upgrade.py::test_splices_refuses_a_hunk_that_no_longer_places_uniquely` |
| the *same manifest* outcome records `[kb] template` under `--apply` and changes nothing else — **the row T4 shipped said the opposite**, and D-16 reversed it: a KB on this path had no command that could clear the warning | D-16 | `tests/test_cli_upgrade.py::test_same_manifest_under_apply_records_the_reference_and_nothing_else` |
| the write on that outcome is announced before it is made, asserted by line position | D-16 | `tests/test_cli_upgrade.py::test_same_manifest_under_apply_announces_the_write_before_making_it` |
| `pnk upgrade` without `--apply` still writes nothing on that outcome | D-16 | `tests/test_cli_upgrade.py::test_same_manifest_without_apply_still_writes_nothing` |
| `--json --apply` emits one document on that outcome too, and the reference is recorded | D-16 | `tests/test_cli_upgrade.py::test_same_manifest_under_apply_json_reports_the_write` |
| the backup is named by its **full path** when it does not sit in the KB, which is what a symlinked manifest produces | T4 | `tests/test_cli_upgrade.py::test_the_backup_is_named_by_its_full_path_when_it_leaves_the_kb` |

## An unbuilt vector tier is refused rather than ignored (T5)

| What must be true | Increment | Test |
|---|---|---|
| a manifest cannot name a vector tier that is not built — and the message shows `sqlite-vec` as the value **found**, never as a comma-followed member of the accepted list, which is exactly what the pre-fix text was | T5 | `tests/test_manifest.py::test_an_unbuilt_vector_tier_is_refused_with_the_tier_that_is_built` |
| the fix is in the error the user sees: it names `docs/STATUS.md` and the one-line remedy — and a *typo* keeps the generic remedy, so the pointer is per removed value rather than per key | T5 | `tests/test_manifest.py::test_the_manifest_error_names_docs_status` |
| `meta`'s `vector_tier` is written from the resolver's return, not a literal — part 1 pins the shipped `numpy`, part 2 injects a resolver and asserts `meta` follows it. **Not** "the index records the tier that ran": with one tier there is nothing to discriminate, and the stronger promise waits for the tier | T5 | `tests/test_sync.py::test_the_index_records_the_tier_that_ran` |

## A template declares its own files, and `pnk templates` lists them (T7)

| What must be true | Increment | Test |
|---|---|---|
| an absent `files` key still copies the two files that were hardcoded before it existed — absent means those two, never none | T7 | `tests/test_init.py::test_a_template_without_a_files_key_still_copies_the_historical_two` |
| a declared list is copied and an undeclared file in the same tree is not — the third file is the discriminator, without which the test passes under an implementation that ignores `files` | T7 | `tests/test_init.py::test_a_declared_file_list_is_copied_and_an_undeclared_file_is_not` |
| **a template cannot declare a file inside the version archive** — asserted on the archive rule's own words, because containment lets this entry through: it lands *inside* the target, so a test satisfied by any `TemplateError` stays green with no archive rule at all | T7 | `tests/test_init.py::test_a_files_entry_naming_the_version_archive_is_refused` |
| **a template file entry cannot write outside the KB**, lexically — `../../evil.md` | T7 | `tests/test_init.py::test_a_template_file_entry_that_escapes_the_target_is_refused` |
| ...and on disk — a symlinked directory *in the target*, which is what a KB adopted from an existing directory presents. **A separate test, because the mutation pass showed why**: with both cases in one test, removing the destination check turned it red on the lexical assertion and the symlink case never ran | T7 | `tests/test_init.py::test_a_symlinked_directory_in_the_target_is_refused` |
| a template file entry cannot **read** outside the template — a symlinked directory in the template tree lands its destination inside the KB, so the write-side check cannot see it. The plan named this case in its test list while its rule sentence covered only the target; both layers are built | T7 | `tests/test_init.py::test_a_template_file_entry_that_reads_outside_the_template_is_refused` |
| the extracted landing predicate keeps its four hard-won cases: a `..` that stays inside is accepted, one that walks out is refused, a symlinked leaf stays readable, a symlinked ancestor is caught, a trailing `..` is refused, and an unreadable path raises rather than answering `False` | T7 | `tests/test_paths.py::test_a_dot_dot_that_stays_inside_is_accepted`, `tests/test_paths.py::test_a_dot_dot_that_walks_out_is_refused`, `tests/test_paths.py::test_a_symlinked_leaf_stays_readable`, `tests/test_paths.py::test_a_symlinked_ancestor_is_caught`, `tests/test_paths.py::test_a_trailing_dot_dot_is_refused`, `tests/test_paths.py::test_an_embedded_nul_raises_rather_than_answering_false` |
| the extraction is behaviour-preserving | T7 | **none of its own** — held by the existing `[sources] include` containment tests passing **unchanged**, which is a property of the diff rather than of any assertion. `uv run pytest -k 'inside or escape or dot_dot' tests/test_sync.py tests/test_manifest.py` reports 9 passing; a new test here would only restate them |
| `pnk init` honours a declaration end to end — the nested entry's directory is created, the undeclared file is not copied, and the historical pair is not implied once a list exists. Every other `files` row calls `copy_extras` directly, so without this one it could be handed the wrong target, or stop being called, with all of them still green | T7 | `tests/test_init.py::test_init_stamps_the_files_a_template_declares` |
| **a template cannot change what it stamps without a version bump** — `files` is folded into the drift gate's content hash, the one behaviour-bearing key in the file that hash excludes | T7 | `tests/test_template_drift.py::test_declaring_a_files_list_without_bumping_the_version_fails_the_gate` |
| ...and nothing else in `template.toml` is folded in, which is what keeps leg (ii) able to fail — hashing `version` would make every bump change the hash by construction | T7 | `tests/test_template_drift.py::test_the_rest_of_template_toml_stays_outside_the_hash` |
| an absent `files` key hashes differently from an empty one, so every hash published before T7 stays valid and `[]` is not read as "the historical two" | T7 | `tests/test_template_drift.py::test_an_absent_files_key_hashes_differently_from_an_empty_one` |
| `pnk templates` lists the shipped template with its version and description | T7 | `tests/test_cli.py::test_pnk_templates_lists_notes_with_its_version` |
| `--json` and the human listing are two renderings of one answer, and `reference` agrees with its parts | T7 | `tests/test_cli.py::test_pnk_templates_json_matches_the_human_output` |
| it takes no `--kb` — the listing is a property of the install, and the obvious "fix" would make it look KB-dependent | T7 | `tests/test_cli.py::test_pnk_templates_takes_no_kb_flag` |

## `pnk ask` — the free question surface (E1)

| What must be true | Increment | Test |
|---|---|---|
| a confident KB gets cited evidence, the confidence line, and the **one-call** sizing — and the run leaves no ledger, which is what spending looks like on disk. It cannot fail while no paid code exists: it is a tripwire for E4, which adds a loop to this same command | E1 | `tests/test_cli_ask.py::test_a_confident_kb_gets_cited_evidence_and_the_price_of_one_call` |
| low confidence is sized as decomposition and repeated search, **not** as one call — the branch that decides what a paid run would cost | E1 | `tests/test_cli_ask.py::test_a_low_confidence_kb_is_told_it_would_take_decomposition_not_one_call` |
| an uncalibrated KB runs anyway and names `python -m pinakes.calibrate` — **once**, in one sentence covering all three `unknown` causes, because `confidence_reason` already discriminates them and a second copy of that logic could disagree with the first (D-22 option E) | E1 | `tests/test_cli_ask.py::test_an_uncalibrated_kb_names_the_calibration_module_in_one_sentence` |
| the other two `unknown` causes behave identically — a reranker the thresholds were not fitted for, and reranking switched off with thresholds present | E1 | `tests/test_cli_ask.py::test_a_reranker_the_thresholds_were_not_fitted_for_is_uncalibrated_too`, `tests/test_cli_ask.py::test_thresholds_with_reranking_switched_off_are_uncalibrated_too` |
| a question **nothing matches** is not sent off to calibrate: `_confidence` returns `unknown` for an empty result even on a fitted KB, so without its own branch a correctly-calibrated user would be told to calibrate | E1 | `tests/test_cli_ask.py::test_a_question_nothing_matches_is_not_told_to_calibrate` |
| **every confidence branch offers `--deep`, and the parser accepts it** — E1 printed the release's name and no command line because the flag did not exist; the rule was *name only what this build can do*, so E4 both implements it and prints it | E1, E4 | `tests/test_cli_ask.py::test_every_confidence_branch_offers_the_flag_that_now_exists` |
| `pnk search`'s escalation notice names only what can be typed — it advertised `pnk ask --deep`, neither a command nor a flag, in the sentence this test is named for | E1 | `tests/test_cli_search.py::test_an_uncalibrated_kb_says_so_without_naming_a_command_that_does_not_exist` |
| `--json` is `search`'s payload plus `answer: null` and an `escalation` block, and `branch` really varies with confidence — a consumer discriminates on the field, never on the sentence | E1 | `tests/test_cli_ask.py::test_json_carries_a_null_answer_and_an_escalation_block`, `tests/test_cli_ask.py::test_the_escalation_branch_discriminates_the_confidence_value` |
| the two surfaces render one retrieval — same confidence, same citations, same sizing sentence | E1 | `tests/test_cli_ask.py::test_json_and_the_human_output_agree_on_confidence_and_citations` |
| every filter `pnk search` takes, `pnk ask` takes (D-27) — asserted in **both** directions, because a filter wired to nothing narrows everything to nothing | E1 | `tests/test_cli_ask.py::test_every_filter_reaches_the_pipeline`, `tests/test_cli_ask.py::test_the_tag_filter_keeps_a_document_that_carries_the_tag`, `tests/test_cli_ask.py::test_k_bounds_how_many_passages_come_back` |
| the free-path gate covers `pnk ask` from the increment that creates it, and covers it by **matching its output** — no module row in `test_paid_path.py` could tell that call from `pnk search`'s, so deleting the line would leave every row green | E1 | `tests/free_path_run.py` (asserted inside `_run_free_surfaces`), driven by `tests/test_paid_path.py::test_the_free_path_never_imports_the_paid_client` |

## The deep client, and what it will not let a caller get wrong (E3)

Every row below is driven by `tests/fixtures/deep/`, with `anthropic` **not installed** — the seam
`extract/claude.py` proved, reused rather than reinvented.

| What must be true | Increment | Test |
|---|---|---|
| a fixture transport drives a whole round — decompose, then answer — and the ledger closes a reconciled pair for each call | E3 | `tests/test_deep_client.py::test_a_fixture_transport_drives_a_whole_round` |
| the key is `PINAKES_ANTHROPIC_API_KEY`, and an ambient `ANTHROPIC_API_KEY` is **not** enough — asserted again on the second entry point, because "the extractor refuses it" says nothing about a new module | E3 | `tests/test_deep_client.py::test_an_ambient_anthropic_api_key_is_not_enough`, `tests/test_deep_client.py::test_the_key_is_read_from_the_pinakes_variable` |
| a missing key names **this** command, not the extractor — someone who typed `pnk ask --deep` and is sent to `[extraction]` has been sent to the wrong file | E3 | `tests/test_deep_client.py::test_a_missing_key_refuses_naming_this_command_not_the_extractor` |
| `api_key=` is passed explicitly, and `anthropic` is imported inside the transport rather than at module scope | E3 | `tests/test_deep_client.py::test_the_transport_passes_api_key_explicitly_never_omitting_it`, `tests/test_deep_client.py::test_anthropic_is_imported_inside_the_transport_and_nowhere_else` |
| a refusal and a truncation **billed**, so both are reconciled rather than voided — and a truncation is named before the body is parsed, because a truncated response is also invalid JSON | E3 | `tests/test_deep_client.py::test_a_refusal_is_billed_reconciled_and_reported`, `tests/test_deep_client.py::test_a_truncation_is_billed_and_named_before_the_body_is_parsed` |
| a 429 never billed, so it is **voided** and re-sent under a fresh reservation; exhausted attempts leave every reservation released at zero | E3 | `tests/test_deep_client.py::test_a_not_billed_failure_is_voided_and_retried`, `tests/test_deep_client.py::test_transport_attempts_are_bounded_and_every_one_is_voided` |
| a timeout is billable-unknown, so its reservation is left **open** for `pnk budget --resolve` rather than voided | E3 | `tests/test_deep_client.py::test_a_timeout_is_left_unresolved_rather_than_voided` |
| a cap refuses **before** the call, so the transport is never touched and no reservation is written | E3 | `tests/test_deep_client.py::test_the_budget_refuses_before_any_call_is_made` |
| the decomposition schema has one field, an array of plain strings — a steered model has nowhere to put a path, a filter or a KB selector (§5's structural half; the behavioural half is E4's) | E3 | `tests/test_deep_client.py::test_the_decomposition_schema_gives_a_model_nowhere_to_put_a_path`, `tests/test_deep_client.py::test_an_injected_subproblem_arrives_as_nothing_but_a_search_string` |
| a citation naming a passage the call never saw is **refused, not dropped** — dropping leaves prose whose support has silently disappeared while the remaining numbers still make it look sourced | E3 | `tests/test_deep_client.py::test_a_citation_naming_a_passage_the_call_never_saw_is_refused`, `tests/test_deep_client.py::test_every_out_of_range_citation_is_refused`, `tests/test_deep_client.py::test_a_boolean_citation_is_not_passage_one` |
| the three bounds E2's price assumes are enforced where the request is built, not left to the caller: the question ceiling, the carried-memory ceiling, and `final_k` passages per answering call | E3 | `tests/test_deep_client.py::test_a_question_over_the_ceiling_is_refused_before_anything_is_sent`, `tests/test_deep_client.py::test_carried_memory_over_what_a_round_reserved_is_refused`, `tests/test_deep_client.py::test_more_passages_than_the_call_reserved_for_is_refused` |
| the request carries the pinned output shape — `EFFORT` and `THINKING` together, `max_tokens` from the estimator, and none of the three sampling parameters that 400 | E3 | `tests/test_deep_client.py::test_the_request_carries_the_pinned_output_shape` |
| the model is shown the evidence the user reads, numbered the same way — and no document id, which is an identifier it could compose one of | E3 | `tests/test_deep_client.py::test_the_answer_call_shows_the_model_the_evidence_the_user_reads` |
| a reworded prompt or a reshaped schema bumps the version that names it — E6 measures against these, and a transcript naming a version whose text has since moved records nothing (T1's lesson, one module down) | E3 | `tests/test_deep_client.py::test_a_prompt_change_bumps_the_version_that_names_it` |
| the injection rule is in **both** prompts — the decompose call sees carried memory, which is prose an answer call wrote from those same passages | E3 | `tests/test_deep_client.py::test_the_injection_rule_is_in_every_prompt_that_carries_untrusted_text` |
| `max_tokens` is not a knob a caller can raise — it is two thirds of a round's price, and a settable ceiling is a caller-supplied under-reservation | E3 | `tests/test_deep_client.py::test_max_tokens_is_not_a_knob_a_caller_can_raise` |
| an unclassified exception leaves the reservation **open** — a defect is not proof the call never billed, and proof is what a void requires | E3 | `tests/test_deep_client.py::test_an_exception_the_transport_did_not_classify_is_not_voided` |
| a failure **after** the response arrives is not voided either — the gap `response_received()` exists for, and the only place the flag is not inert. Found by mutation at E4: deleting the call broke nothing | E3, E4 | `tests/test_deep_client.py::test_a_failure_after_the_response_arrives_is_not_voided_either` |
| **a Ctrl-C mid-request is not voided either**, on *both* paid clients — the request was sent, so the server may have generated and billed. Found at E4: a `KeyboardInterrupt` fell past `except Exception` into the ledger's `finally`, which voids an unclosed call | E3, E4, I7b | `tests/test_deep_client.py::test_a_keyboard_interrupt_mid_request_is_not_voided_either`, `tests/test_extract_claude.py::test_a_keyboard_interrupt_mid_request_is_not_voided_either` |
| the constructed client really carries `max_retries=0` — the dict is asserted elsewhere, which says nothing about this transport passing it | E3 | `tests/test_deep_client.py::test_the_constructed_client_really_carries_max_retries_zero` |
| the rendered passage envelope stays inside **half** what `PASSAGE_ENVELOPE_TOKENS` reserves — the first draft repeated the path and heading inside a citation line and spent 226 of 250 | E3 | `tests/test_deep_client.py::test_the_rendered_envelope_fits_the_constant_that_prices_it` |
| every fixture says why it exists and where its body came from — the whole set is authored until E6 spends, and only the provenance separates "the branch behaves as the plan says" from "this is what the API returns" | E3 | `tests/test_deep_client.py::test_every_fixture_says_why_it_exists_and_where_its_body_came_from`, `tests/test_deep_client.py::test_the_fixture_set_covers_every_branch` |

## The loop, and what ends a run (E4)

| What must be true | Increment | Test |
|---|---|---|
| a confident question costs **exactly one call** — the cheap branch retrieves nothing of its own, and the estimate checked is `estimate_synthesis` rather than a fraction of a loop | E4 | `tests/test_deep_loop.py::test_a_confident_question_costs_exactly_one_call`, `tests/test_deep_loop.py::test_the_cheap_branch_is_priced_as_synthesis_not_as_a_fraction_of_a_loop` |
| a citation number is resolved back to the **document** it indexed — E3 made this safe by never showing the model an identifier, and E4 owns the mapping | E4 | `tests/test_deep_loop.py::test_a_citation_number_is_resolved_back_to_the_document_it_indexed` |
| a low-confidence run stops at **sufficiency** once the accumulated evidence clears §4.2's threshold — the early stop, and the whole return on having a calibrated signal | E4 | `tests/test_deep_loop.py::test_a_low_confidence_question_stops_at_sufficiency_once_the_evidence_clears_it` |
| an **uncalibrated** run never consults sufficiency at all — scripted to answer `high` and asserted never called, because running it and discarding the answer is indistinguishable from the outside and would stop on a signal the KB does not have (D-22 option E) | E4 | `tests/test_deep_loop.py::test_an_uncalibrated_run_never_consults_sufficiency_and_says_which_bound_ended_it` |
| a run the evidence never satisfies ends at the **round cap** with a best-effort answer, and the label says it was the cap and not sufficiency | E4 | `tests/test_deep_loop.py::test_a_run_the_evidence_never_satisfies_stops_at_the_round_cap` |
| the **cursor never re-asks** a subproblem, however it is re-cased or re-spaced — the ~35% token waste the published artifact this shape comes from measured | E4 | `tests/test_deep_loop.py::test_the_cursor_never_re_asks_a_subproblem_however_it_is_re_spelled` |
| a round whose subproblems match nothing stops rather than paying a decompose call to be told the same thing again | E4 | `tests/test_deep_loop.py::test_a_round_whose_subproblems_match_nothing_stops_rather_than_paying_to_ask_again` |
| each round carries forward what the last one established — round 2's decompose call *sees* round 1's answer, or the loop is two independent questions sharing a budget | E4 | `tests/test_deep_loop.py::test_each_round_carries_forward_what_the_last_one_established` |
| the whole operation is refused **before round 0**, naming every blocked window at once with the complete `[budget]` edit — and reserving nothing | E4 | `tests/test_deep_loop.py::test_the_whole_operation_is_refused_before_round_zero_naming_every_blocked_window` |
| a **stock KB** is admitted by the defaults D-30 raised — the case the old 0.30 cap refused, which was D-22 option A's outcome arriving through the caps | E4 | `tests/test_deep_loop.py::test_a_stock_kb_is_admitted_by_the_defaults_the_release_raised`, `tests/test_deep_estimate.py::test_the_shipped_defaults_now_leave_the_whole_loop_inside_every_budget_window` |
| a mid-loop halt under `on_exceed = "partial"` keeps the rounds already paid for, labelled; under `abort` it returns no answer and still leaves them reconciled (D-23 option A) | E4 | `tests/test_deep_loop.py::test_a_halt_mid_loop_keeps_what_the_earlier_rounds_paid_for_when_on_exceed_is_partial`, `tests/test_deep_loop.py::test_the_same_halt_under_abort_returns_no_answer_at_all` |
| a timeout mid-loop leaves its reservation **unresolved** rather than voided — a void needs proof the call never billed | E4 | `tests/test_deep_loop.py::test_a_timeout_leaves_the_reservation_unresolved_rather_than_voided` |
| every call is reserved and reconciled one at a time, all under one `operation_id` recorded as `ask` (M9 — no ledger change) | E4 | `tests/test_deep_loop.py::test_every_call_is_reserved_and_reconciled_one_at_a_time` |
| the `confirm_above_eur` prompt is put **once** for the whole run, and a `no` — or an unattended run without `--yes` — spends nothing | E4 | `tests/test_deep_loop.py::test_the_confirmation_is_put_once_for_the_whole_run_and_a_no_spends_nothing`, `tests/test_deep_loop.py::test_an_unattended_run_without_yes_refuses_rather_than_spending`, `tests/test_cli_ask.py::test_deep_needs_a_yes_when_nothing_can_answer_the_prompt` |
| a question nothing matched is refused rather than answered cheaply, and one over the character ceiling is refused **before** the run is priced | E4 | `tests/test_deep_loop.py::test_a_question_nothing_matched_is_refused_rather_than_answered_cheaply`, `tests/test_deep_loop.py::test_a_question_over_the_ceiling_is_refused_before_the_run_is_even_priced`, `tests/test_cli_ask.py::test_a_question_nothing_matched_is_refused_before_anything_is_sent` |
| **§5's retrieval rule** — a subproblem reaches `search()` as a query string and nothing else, against the hostile fixture. E4's half of the two-part defence; E3 owns the schema half | E4 | `tests/test_deep_loop.py::test_a_subproblem_reaches_retrieval_as_a_query_string_and_nothing_else`, `tests/test_deep_loop.py::test_the_answering_call_is_told_the_passages_are_evidence_not_instructions` |
| the carried memory is **re-folded**, never appended: it never exceeds what a round was priced for, keeps the newest rounds, reads oldest first, and truncates rather than drops a single oversized round | E4 | `tests/test_deep_loop.py::test_the_carried_memory_never_exceeds_what_a_round_was_priced_for`, `tests/test_deep_loop.py::test_the_re_fold_keeps_the_newest_rounds_and_reads_oldest_first`, `tests/test_deep_loop.py::test_a_single_round_larger_than_the_whole_budget_is_truncated_not_dropped` |
| the round cap that is **priced** is the round cap that **runs** — both read off `[deep] max_rounds` in one place | E4 | `tests/test_deep_loop.py::test_the_loop_prices_the_round_cap_it_will_actually_use` |
| **every stop reason has a sentence of its own, and an unknown one raises** — the chain used to default to the round-cap sentence, so a reason added later would have rendered as a confident, wrong claim about which bound ended a paid run | E4 | `tests/test_deep_loop.py::test_every_stop_reason_has_a_sentence_of_its_own` |
| the *"no calibrated signal"* sentence appears on an uncalibrated run and on no other — it rides on the branch, not on the stop reason | E4 | `tests/test_deep_loop.py::test_only_an_uncalibrated_run_is_told_its_signal_is_missing` |
| `pnk ask --deep` answers through the real command, prints the free evidence above the answer, and says what it cost; `--json` carries an `answer` **object** where the free form carries `null` | E4 | `tests/test_cli_ask.py::test_deep_on_a_confident_kb_answers_in_one_call_and_says_what_it_cost`, `tests/test_cli_ask.py::test_the_json_answer_object_carries_the_blocks_the_citations_and_the_money`, `tests/test_cli_ask.py::test_deep_on_an_uncalibrated_kb_runs_and_names_the_bound_that_ended_it` |
| the free `pnk ask` **prices** the run it offers, and degrades to no number rather than failing when the estimate refuses — while `--deep` on the same KB refuses instead of guessing | E4 | `tests/test_cli_ask.py::test_the_free_command_prices_the_run_it_offers`, `tests/test_cli_ask.py::test_a_price_it_cannot_compute_leaves_the_free_command_working` |
| `-k` narrows the paid run's price, not only its evidence (D-27) | E4 | `tests/test_cli_ask.py::test_every_filter_still_narrows_the_paid_run` |
| **`pnk ask` without `--deep` spends nothing on any confidence value** — no ledger, and no transport ever built. The two halves share `_retrieval` and one `if` decides between them, so both directions are asserted rather than one | E4 | `tests/test_cli_ask.py::test_the_free_command_spends_nothing_on_any_confidence_value` |
| the free path reaches `pinakes.deep.estimate` and **still** never `pinakes.deep.client` — observed in a fresh subprocess, with the positive half asserted too: the client's absence alone is also true of a run that priced nothing | E4 | `tests/test_paid_path.py::test_the_free_path_reaches_the_estimator_and_still_not_the_client` |
| a paid run that produced **no answer** exits non-zero and says so on both surfaces — the calls were billed and reconciled, but a command asked a question and answered none must not report success to a script | E4 | `tests/test_cli_ask.py::test_a_paid_run_that_produced_no_answer_exits_non_zero_and_says_so`, `tests/test_cli_ask.py::test_the_json_surface_reports_the_same_outcome_as_the_human_one` |
| **no document quotes a sentence this build can no longer print** — a fenced block showing an older build's output is correct Markdown, so no link check, name check or `mkdocs --strict` run can see it. Twice now: E1 and E4 left the same GUIDE block stale | E4 | `tests/test_docs_quote_the_shipped_sentences.py::test_no_document_still_quotes_a_sentence_this_build_cannot_print` |
| an `ask` operation is totalled **beside** a `sync` one on the same day, in its own row — M9's claim that a non-sync operation needs no ledger change, verified rather than assumed. Closes the second half of E5 at E4 | E4, E5 | `tests/test_cli_budget.py::test_an_ask_operation_is_totalled_beside_a_sync_one_on_the_same_day` |
| a paid run leaves a transcript at `.pinakes/deep/<operation_id>.json` and **names it in the output**, and a free `pnk ask` leaves none — the directory is never even created | E5 | `tests/test_cli_ask.py::test_a_paid_run_leaves_a_transcript_and_says_where`, `tests/test_cli_ask.py::test_a_free_ask_writes_no_transcript` |
| the transcript is filed under the **same `operation_id` the ledger recorded**, which is the join a `pnk budget` row needs — the ledger stores no query text, so the row and the file meet on the id or not at all | E5 | `tests/test_cli_ask.py::test_the_transcript_is_filed_under_the_operation_id_the_ledger_recorded`, `tests/test_deep_transcript.py::test_a_transcript_lands_under_its_own_operation_id_and_reads_back` |
| it records what the run was **asked**, not only what it answered: the question, the filters as typed, the confidence reading that chose the branch, and the prompt and schema versions that produced the prose | E5 | `tests/test_deep_transcript.py::test_the_envelope_records_what_the_run_was_asked_not_only_what_it_answered`, `tests/test_cli_ask.py::test_the_transcript_records_the_filters_the_run_was_narrowed_by` |
| the stored `answer` object is **the one `--json` prints** — one renderer, two consumers, because two copies would drift silently while both stayed valid JSON | E5 | `tests/test_cli_ask.py::test_the_transcripts_answer_object_is_what_json_printed` |
| a run that made calls and produced **no answer** still leaves one — the case the record is worth most in, since nothing on screen explains the `pnk budget` row | E5 | `tests/test_cli_ask.py::test_a_paid_run_with_no_answer_still_leaves_a_transcript` |
| a run **nothing authorised** leaves none: it is written after `run_deep` returns, so a budget refusal, a declined confirmation and an `abort` halt all raise past it | E5 | `tests/test_cli_ask.py::test_a_run_that_was_never_authorised_writes_no_transcript` |
| nothing can file a transcript under a name that is not a ULID — `Accountant` mints the id, but it is also a *parameter*, and a caller-supplied path component must never name a directory above `.pinakes/deep/` | E5 | `tests/test_deep_transcript.py::test_a_transcript_cannot_be_filed_under_anything_but_a_ulid`, `tests/test_deep_transcript.py::test_a_body_with_no_operation_id_is_refused_rather_than_filed_somewhere` |
| a transcript is **spared by the sweep and by `--rebuild`**, and by `--clear-cache` in both its spellings — D-26's protection, and the property a later increment moving the directory would break while every content test still passed | E5 | `tests/test_deep_transcript.py::test_a_sync_sweeps_orphaned_cache_entries_and_leaves_the_transcript`, `tests/test_deep_transcript.py::test_a_rebuild_leaves_the_transcript_alone`, `tests/test_deep_transcript.py::test_clearing_the_extraction_cache_never_touches_a_transcript` |
| `--clear-cache=transcripts` removes them and **only** them, asks first without `--yes`, and refuses unattended naming its own flags rather than the cache's | E5 | `tests/test_deep_transcript.py::test_clearing_transcripts_never_touches_the_extraction_cache`, `tests/test_deep_transcript.py::test_clearing_transcripts_without_a_yes_asks_first_and_removes_nothing`, `tests/test_deep_transcript.py::test_the_cli_refuses_unattended_without_a_yes_and_names_the_flags_that_would_work` |
| the interactive confirm-then-re-call path carries the **target the prompt described**, on either store — the path `sys.stdin.isatty()` had kept untested since I4 | E5 | `tests/test_deep_transcript.py::test_a_confirmed_prompt_removes_the_transcripts_and_nothing_else`, `tests/test_deep_transcript.py::test_declining_the_prompt_removes_nothing`, `tests/test_deep_transcript.py::test_a_confirmed_cache_clear_still_leaves_the_transcript` |
| a write killed before `os.replace` leaves a file the readers cannot mistake for a finished transcript — asserted on the name the writer actually uses, not on one the test invented | E5 | `tests/test_deep_transcript.py::test_a_half_written_transcript_is_never_counted_as_a_finished_one` |
| a `--deep` run ends by **printing** the `links[]` entries its own citations propose — the sidecar to paste into, the URI, `rel: co-cited` and `origin: deep` — and nothing is written | E7 | `tests/test_cli_ask.py::test_deep_ends_by_printing_the_links_its_own_citations_propose`, `tests/test_deep_suggest.py::test_two_documents_cited_in_one_block_propose_one_link`, `tests/test_deep_suggest.py::test_the_fragment_names_the_sidecar_and_both_documents` |
| **a document instructing the model to link elsewhere produces no such suggestion.** Driven through a whole run: the hostile text reaches the model and the model obeys it in prose, and the named document is real, with a sidecar — so containment, existence and the ULID check all pass for it and only the citation rule can keep it out | E7 | `tests/test_deep_suggest.py::test_an_instruction_in_a_document_to_link_elsewhere_produces_no_such_suggestion` |
| **a suggestion naming a document the run never retrieved is refused**, at either endpoint. Reachable only because `co_citations` and `propose` are separate: handed only pairs its own expression built, a missing guard is indistinguishable from a working one | E7 | `tests/test_deep_suggest.py::test_a_suggestion_naming_a_document_the_run_never_retrieved_is_refused`, `tests/test_deep_suggest.py::test_a_pair_whose_source_the_run_never_retrieved_is_refused_too` |
| **the printed fragment parses as YAML, round-trips through `ruamel` byte for byte, and survives being pasted** into a real sidecar — `read()` sees the link, `write()` leaves the file identical, and `origin: deep` is still there, which holds only because `_merge_links` never touches the rest of a matched entry | E7 | `tests/test_deep_suggest.py::test_the_printed_fragment_parses_as_yaml_and_round_trips_through_ruamel_unchanged`, `tests/test_deep_suggest.py::test_the_printed_fragment_survives_being_pasted_into_a_sidecar` |
| an endpoint is resolved through the **existing** containment check, so a citation whose path escapes the KB, whose document has been deleted, or whose sidecar no longer carries the id the run retrieved is dropped rather than raised — this runs after the money is spent | E7 | `tests/test_deep_suggest.py::test_a_citation_pointing_outside_the_kb_is_dropped`, `tests/test_deep_suggest.py::test_a_document_deleted_since_the_run_is_dropped_rather_than_raised`, `tests/test_deep_suggest.py::test_a_sidecar_whose_ulid_no_longer_matches_the_run_is_dropped` |
| the suggested direction is a property of the **paths**, not of mint order or of which passage the model cited first — pinned by a fixture whose ULIDs ascend in the opposite order to its paths, without which three direction tests could not tell the two apart | E7 | `tests/test_deep_suggest.py::test_the_direction_does_not_depend_on_the_order_the_model_cited_in`, `tests/test_deep_suggest.py::test_the_fixture_mints_ids_in_the_opposite_order_to_the_paths` |
| a pair already linked in that sidecar is not proposed, a document cited alone proposes nothing, and a run with no pair prints **no section at all** rather than an empty one | E7 | `tests/test_deep_suggest.py::test_a_pair_already_linked_in_the_source_sidecar_is_not_proposed`, `tests/test_deep_suggest.py::test_a_document_cited_alone_proposes_nothing`, `tests/test_cli_ask.py::test_a_run_whose_citations_name_one_document_prints_no_suggestion_section` |
| a sidecar that already carries `links:` is given entries **without a second key** — two `links:` in one mapping is a YAML duplicate key, which ruamel refuses outright | E7 | `tests/test_deep_suggest.py::test_a_sidecar_that_already_has_links_is_given_entries_without_a_second_key` |
| `--json` carries a `suggestions` object holding **the same fragment the human surface prints**, and `null` when nothing was paid for — the promise `answer` and `transcript` already make | E7 | `tests/test_cli_ask.py::test_the_json_suggestions_object_carries_the_fragment_the_human_surface_prints`, `tests/test_cli_ask.py::test_a_free_ask_suggests_nothing`, `tests/test_cli_ask.py::test_json_carries_a_null_answer_and_an_escalation_block` |
| the shipped `rel` and `origin` are the values the design names, and `docs/CLI.md` quotes the header this build prints — both spelled out literally, because every other assertion imports the constant it checks and the mutation pass proved that catches nothing | E7 | `tests/test_deep_suggest.py::test_the_shipped_relation_and_provenance_are_the_values_the_design_names`, `tests/test_deep_suggest.py::test_the_documentation_quotes_the_header_this_build_prints` |
