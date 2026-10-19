# Learner-data upkeep

Production and staging closeout audit: 17 October 2026. Full snapshots and
verification are in workspace `audits/upkeep-closeout-20261017/`.

The live accounts are Joshua, Diego, Artis, SafariMS and JP; staging has joshua.
Joshua, JP and Diego have their restored progress. SafariMS keeps full admin
access. On 18 October its learning state was replaced with a verified Joshua
snapshot: 10,374 progress entries, matching settings and two saved song sets.
Prior test state is archived; original live review events are retained. Detailed
Joshua review history remains with Joshua and the archive, rather than being
duplicated into SafariMS. Metadata records the imported counter baseline.
Evidence: workspace `audits/safarims-copy-20261018/`.

## Supported state

- Item identity is `(user_id, lang_code, item_id, mode)`; component types remain
  word, sense, mwe, clitic or lemma. Card identities and history are retained.
- Counts are nonnegative integers. An answered card's explicit stage is 1–9;
  stage zero is only for cards with no correct answer. NULL derives the stage.
- App and Worker share `srs-policy.js`. Latest answer dates determine unresolved
  mistakes. Joshua's imported known cards retain a distinct 28 October review
  date until a real answer clears it; answer dates are not shifted.
- Missing historical `last_seen_at` remains explicitly absent. All 5,682 such
  rows have genuine answer dates and valid schedules; no new exposure is invented.
- Old counters and detailed event history are not guaranteed to match. The
  closeout retained 13 Joshua, 78 JP, 2 Diego and 1 SafariMS differences. Preserve
  the stronger recorded counts and original events; never invent individual
  historical answers or lower totals to force equality. These are declared
  compatibility records, not a reason to delete learning progress.
- Cumulative-counter sync prevents stale count/date regressions. Coalesced
  offline payloads must update the durable and in-memory operation together;
  an in-flight operation cannot absorb a later answer. Retried extended payloads
  append events using lifetime count ordinals rather than starting at zero again.
  This does not claim perfect reconciliation of simultaneous offline answers
  made independently on multiple devices; that needs an individual-event protocol.

## Verification and cleanup

All 10,790 current state rows (10,789 production + 1 staging) passed the real
shared scheduling/client reachability check. Full and delta Worker read handlers
were verified against fresh live snapshots for every account, including empty
deltas at the current watermark. This was not a physical phone sign-in test.
No invalid counts/stages, malformed identities/timestamps, invalid metadata JSON,
broken flag/event ownership links or events lacking current state were found.

Twelve reappeared user_meta rows belonging to retired JST were snapshotted and
removed with exact row guards after confirming there was no JST profile or
progress. All active users' state, events, settings, playlists and flags were
verified unchanged; staging was unchanged. Both environments now have zero
unregistered data owners in the audited tables. The original archive is intact.

Regression checks are `tests/app/test_upkeep.py`, `test_progress_migration.py`
and `test_upkeep_queue.py`. The final queue fix is staged/reviewed through the
normal AIRLOCK process; publication receipts belong with the closeout evidence.
Do not apply old migration 0008 blindly: it embeds the superseded scheduling
ladder. Future repairs must use the current shared policy and guarded snapshots.
