# Passwordless demo accounts

The live GitHub Pages app and staging both use the Fluency Clerk development
instance, Google and Microsoft sign-in, and email verification codes. Google is
the primary option; Microsoft and email appear under More sign-in options.
Sign-up is a separate, matching screen. Try as guest allows account-free
exploration without saving progress. Password creation is disabled. This is intentionally Clerk's development setup for
Josh's small demo, not a configured Clerk production instance.

New verified users choose a username once. The username field starts empty;
there are no owner-specific suggestions. Names are labels, never evidence of
ownership of historical data. Existing verified accounts restore their own
registered profile after sign-in.

The frontend key is public. `jose` verifies session signatures, issuer, expiry,
activation time and the allowed origin. The authenticated account endpoint
chooses the storage identity from the verified session. The production worker
uses `clerk_<user_id>`; the isolated staging worker uses `stg_clerk_<user_id>`.
All progress identities, including bulk rows, must belong to that session.
Profile-directory and database-dump actions are unavailable in this setup.

Staging writes route to `fluency-auth-staging` even if a stale configuration
contains the old production endpoint. URL comparisons are normalized, including
trailing slashes, before a session token is attached. Production writes route to
`fluency-api`. Both APIs reject unauthenticated writes, including old clients.

## Archived accounts

On 13 October 2026 Josh authorized archiving all five remaining legacy accounts
and their staging copies, deleting their live records, then recreating selected
accounts before restoring their data. The complete verified temporary store is
in the workspace under `audits/account-migration/`. It contains a full SQL
export, a restored SQLite database, manifest and deletion verification. All
31,099 progress/component entries and associated history and settings are
preserved. The live databases started empty after this operation.

Do not restore data from a matching display name automatically. Obtain Josh's
identification of the new account and its source archive before restoring it.
Keep copied/synthetic history distinguishable, preserve the archive and verify
all restored counts. Reviewer privileges also need to be assigned explicitly to
the approved new identity rather than inferred from the username JOSHUA.

## No paid services

Do not add payment details, paid add-ons or upgrade a plan without Josh's
explicit approval. Clerk's development-instance limit is 100 users, distinct
from the free Hobby production allowance of 50,000 monthly retained users.
Development email delivery also has limits. Terms can change; stop or replace
this setup rather than authorizing charges if the free tier stops fitting.

## Deploy and review

Install worker dependencies with `npm ci --prefix backend/worker`. Deploy the
staging worker using `wrangler.auth-staging.toml` and the production worker using
`wrangler.toml`. Follow AIRLOCK for the frontend: stage, verify the exact build,
then promote only with Josh's production authorization.

The sign-in panel includes a temporary notice that iCloud/me.com email codes
are affected by Clerk’s development-email delivery incident. Recheck Clerk’s
status before removing the notice. Microsoft uses shared development OAuth
credentials; its button and provider redirect have been checked, but a full
Microsoft account sign-in still needs a user test.

Test Google, Microsoft and email-code sign-in, explicit username registration, remembered
sessions, logout, cross-device progress and isolation between environments.
Use a private browser window to test the provider-choice screen; use a different
email address for a distinct new account. Choosing the same verified email can
resolve to the existing Clerk account. Do not create test users or control
Josh's screen unless authorized.

Before a formal Clerk production deployment, configure an owned domain and
production Google credentials as required by Clerk's deployment documentation.
