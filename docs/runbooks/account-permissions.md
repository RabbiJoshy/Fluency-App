# Account permissions after passwordless migration

Approved role mapping, 17 October 2026:

| Account | Clerk storage identity | Access |
| --- | --- | --- |
| SafariMS (formerly safari) | clerk_user_3KkMOyRxK2i4qZlXgT5VHJRmNTT | Admin tools, flagging, authenticated database exports |
| Joshua | clerk_user_3KdfOQ19QCngxtBsj0NsX3qlMjl | Normal learner interface plus reviewer/flagging tools |
| JP | clerk_user_3KllLK7ajq5RWtvjlNdrCH2PTLk | Normal learner interface plus reviewer tools and simple flag actions |
| Other accounts | Any other identity | Normal learner |

`app/js/account-permissions.js` is the shared app/Worker policy. A staging
identity uses the same Clerk subject with `stg_` storage prefix and the same role,
while progress remains isolated. Display names, sign-in provider labels, old JST
initials and copied progress do not grant privileges. SafariMS is also the designated backup identity; Josh explicitly deferred the
Joshua progress copy on 17 October. Its admin access is already assigned. New or recreated Clerk
subjects require an explicit role mapping; copying learning data alone never
copies admin rights.

The Worker verifies the session before checking flag access or admin exports.
Authenticated learners can access only their own learning data. Only the admin
can use database-wide exports; legacy name-based profile-claim actions remain
unavailable. A flag-ID replay cannot modify another account's flag.

The quick “Wrong meaning in this example” action uses the visible meaning and
cycled example, captures the exact example object plus text, translation, IDs,
sense and release/deck provenance, and uses the existing durable offline queue.
Whole-card flags remain available. Flag content is unchanged by role assignment.

Verification: `tests/app/test_steward.py` runs signed-session production/staging
role checks, spoofed-name/ownership rejection, guest/sign-out helpers, real
quick-report capture for a second meaning/cycled example, and real flag SQL
ownership checks against SQLite. Review the staged UI signed in as SafariMS,
Joshua/JP and an ordinary learner before promoting. Physical account sign-ins
remain a user check; these tests do not claim they performed a real provider login.

Production rename evidence and restore backups are outside Git in workspace
`audits/steward-20261017/` and `audits/restore-jp-diego-20261017/`.
