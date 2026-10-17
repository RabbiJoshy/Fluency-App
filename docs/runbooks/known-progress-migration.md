# Known-progress migration

Approved by Josh on 14 October 2026. Joshua is the target learning identity;
JoshuaBackup is a one-time exact copy after its new verified login is created.
JP keeps counts and genuine dates; only impossible states are repaired. DRG's
32 archived rows remain available. Do not infer ownership from a display name.

The rules are: correct once with no wrong = known; any latest correct = known;
latest wrong or only wrong = practice; no answers = new. When answer order is
absent, any correct is the agreed known fallback. Preserve counts and events.
Known imports get migration_review_at = migration time + 14 days, separately
from last_correct_at. New answers clear this date. The app and Worker import
one shared nine-stage adaptive policy; no correctly answered card uses stage
zero, even when the incoming client supplied it. Old retries cannot reduce
counts or replace newer answer dates.

Prepare a fresh consistent export, restore it to a local SQLite database and
run scripts/prepare_progress_migration.py with --current, --baseline (the saved
13 October Joshua restoration), --original (untouched JST archive), --owner,
--output (outside git), and --at (actual UTC migration time). This never accesses
the live database. Preview category totals and up to three examples each.
Run it against the new export, not yesterday's rehearsal. SQL updates are
guarded by exact pre-migration counts, dates, stage and watermark. Changed rows
must be re-read and reviewed; never loosen these guards to overwrite an answer.
The original JST dates replace the earlier copy's invented dates only for
unchanged once-correct copied rows. Other new answers are preserved.

Schema 0009 adds a nullable scheduling column only. Apply it explicitly after
checking existing columns; do not blindly apply the unrelated global 0008
repair. Deploy schema before Worker; stage and test the frontend before live
promotion. Existing frontends ignore the optional field until upgraded.

Simulate the complete owner-scoped conversion in a disposable local clone.
Verify every count, identity, event and other user's row. Confirm written-row
usage before applying; indexes consume writes too. Do not delete original
archives or synthesize missing review events to make counters agree. Preserve
before/after exports, input hashes, guarded SQL and verification results outside
git. Verify full/delta loads and that normal new answers remove the migration
date. A second migration is refused when dates already exist.

Completed 17 October: JP's historical progress was merged into the confirmed new
JP login, and DRG's into Diego, preserving new answers and genuine evidence.
SafariMS is the confirmed admin/backup identity. Josh explicitly deferred copying
Joshua into SafariMS to another day; its present learning data stays unchanged.
When requested, a backup copy transfers learning state, not credentials or role
ownership, and can then evolve independently. Check D1's current write allowance
first: copying Joshua's state and complete event history in one day exceeds the
free daily allowance with the current indexes. Keep all source archives intact.
