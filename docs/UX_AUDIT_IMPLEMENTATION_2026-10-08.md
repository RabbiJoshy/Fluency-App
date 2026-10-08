# UX audit implementation — 8 October 2026

All five recommendations in `UX_AUDIT_2026-10-08.md` have been implemented.

1. Sign-in owns the keyboard, including Enter on Continue after logout.
2. Phrases-panel snapshots store the parent vocabulary identity and omit temporary
   slots. Earlier malformed snapshots recover by their saved word.
3. The first real card reveal shows “← Needs practice · Got it →” outside the
   card. It persists through card changes until an actual grading swipe, then
   is remembered on the device. Keyboard/button grading does not dismiss it.
4. First-run and introductory tutorials cover the essentials. Help retains the
   full card tour. Form errors appear inline beneath the name field, and fields
   explain their purpose directly.
5. Names and birthday day/month look up a shared profile directory. Recognisable
   matches show study languages and date, with explicit continuation or creation
   of a separate UUID-backed identity. Legacy initials keep their progress keys.
   Remembered profiles skip lookup; logout returns to lookup. Resume snapshots
   are isolated by account. No year is collected; this is not secure authentication.

The worker source was retained into `backend/worker/` from the read-only old
repository. The profile schema was added to the existing D1 database; existing
progress, events, settings and playlists were left in place.

Validation: 205 app tests, including SQLite collision/legacy/retry cases and
syntax checking every boot module. Browser checks verified inline feedback,
Enter lookup, exact-match separation, remembered sign-in and account display.
The live API was checked for lookup, legacy study context and invalid dates.
An existing missing brace in Smart Skip was repaired because it stopped the
entire module graph from loading; the new syntax check guards against recurrence.

Changes were delivered in batches. The final profile batch was included in a
concurrent chat's combined commit, then the combined app passed all 205 tests.
Physical-phone gesture testing and a two-device end-to-end progress-sync check
remain outside this verification; local collision checks and live directory
reads succeeded.
