# Fluency progress and learning profiles

Production: https://fluency-api.rabbijoshy.workers.dev

The existing worker was retained from `../Fluency/backend/worker/src/` on
8 October 2026, including its live-playlist handlers. This repository now
owns the worker source and deployment configuration; the old repository
was left untouched. Existing progress, events, settings and playlist protocols
are unchanged.

`learning_profiles` is an additional directory, not authentication. Names and
birthday day/month identify possible matches. An exact match can always create
another UUID-backed progress identity. Birth years are never collected.

Legacy initials are offered with study context and linked only on explicit
recognition. Their existing progress keys are retained; no progress rows are
renamed, copied or deleted. Already remembered users continue without a prompt.

Actions: `lookupProfiles`, `createProfile`, `claimLegacyProfile`. Creation IDs
are supplied by the client and are idempotent across retries. A legacy ID cannot
be claimed under two birthdays, including concurrent claims.

Local development:

```
wrangler d1 migrations apply fluency --local --config backend/worker/wrangler.toml
wrangler dev --local --config backend/worker/wrangler.toml
```

The existing remote database already has migrations 0001–0005. For this
release, apply only the additive profile schema before deploying the worker:

```
wrangler d1 execute fluency --remote --config backend/worker/wrangler.toml --file backend/worker/migrations/0006_learning_profiles.sql
wrangler deploy --config backend/worker/wrangler.toml
```

App tests include profile validation, real SQLite collision handling, legacy
progress preservation and retry behaviour. The worker can be deployed before
the Pages client; older clients keep working.
