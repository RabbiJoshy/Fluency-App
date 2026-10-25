# Stable loading and sign-in — 25 October 2026

Implemented locally; no deployment or real-account writes performed.

## Findings and changes

| Surface | Finding | Change |
| --- | --- | --- |
| Fresh sign-in | Completion saved the account but never dismissed authentication; progress and playlist requests blocked completion. | Dismiss the panel after profile resolution, release auth readiness, and refresh progress/playlists in the background. Deduplicate session callbacks, discard Guest/sign-out races, bound essential reads, and retry profile failures in place. |
| Home/setup | A readiness timeout could render unknown progress as zero; loading could expose an incomplete level/session region. | Await actual progress readiness with a bounded, recoverable wait; show section placeholders for new contexts and retain valid content for refreshes. Reserve example/statistic space. Failed vocabulary reads produce retries rather than false empty levels. |
| Search | Results were empty during index loading; typed input could be overwritten by stale completion. | Reserve result space, retain typed queries, guard request completion, and provide an in-place retry. Measure untransformed layout dimensions so dialog entrance animations do not shrink the reserved box. |
| Music | Artist requests preceded the workspace; late images and catalogue completion needed stable slots. | Open the workspace with artist placeholders, retain the pending search query, keep image aspect ratios, bound catalogue reads, and distinguish failure from an empty catalogue. |
| Song selection | Album controls appeared late; album completion rebuilt checkboxes and lost focus. | Reserve the album control while loading, update only that control, ignore superseded requests, and keep the song DOM/focus intact. |
| Progress overview | Hidden content and changing dialog height moved mobile controls. | Mask unknown counts with placeholders, keep dialog geometry stable, scroll its body, bound vocabulary loading, and retain existing failure/retry and stale-request guards. |
| Study cards | Core card payloads already load behind the session loader; artist images already have reserved geometry. The optional conjugation drawer gave no immediate feedback while fetching. | Retain the existing essential-payload loader and image slots. Open the drawer immediately with a placeholder, an available Close control, bounded loading, and a retry; cancelled requests cannot reopen it. |
| Settings / Saved / review explanations | Content is synchronous or derived from the local snapshot; no additional network-loading skeleton is needed. | Retain existing rendering. |

The shared loading helper marks busy regions, reserves measured space, supports cached content, and prevents an old completion from clearing a newer placeholder. Placeholder animations respect reduced motion. Deployment builds stamp import versions and the service-worker cache together.

## Verification

- The fresh-login regression fails against the original authentication function and passes against the fix with a progress request that never resolves.
- 135 tests passed across passwordless authentication, music navigation, progress overview, estimation, study sessions/resume, JavaScript syntax, home identity, product shell, and deployment stamping.
- `tests/app/loading_layout_browser.cjs` passed in Chromium at 1440 × 1000 and 390 × 844, with 4× CPU throttling, delayed module/style delivery, and delayed images.
- Browser assertions cover duplicate sign-in callbacks, essential account failure/retry, indefinitely pending progress, delayed setup vocabulary, search failure/retry, stable search/progress/music controls, image geometry, song checkbox identity/focus, album failure states, drawer cancellation, overlapping placeholder ownership, timeout recovery, reduced motion, and horizontal overflow.
- Loading and loaded screenshots were visually reviewed. Browser outputs are written to `FLUENCY_REVIEW_DIR`, or a temporary directory by default.
- `git diff --check -- app tests/app` passed.

## Repeating the browser check

Serve `app/` at a local origin and run:

```sh
FLUENCY_TEST_URL=http://127.0.0.1:8876 node tests/app/loading_layout_browser.cjs
```

Playwright must be available to Node (the desktop bundled runtime provides it). Set `CHROME_PATH` when using an installed Chrome rather than Playwright's bundled browser.

Browser tests mock Clerk and the account API and supply controlled vocabulary fixtures. They do not validate live Google/Microsoft/email authentication, production OAuth redirects, or physical-device Safari rendering. A release smoke check should cover those real integrations.

## Follow-up: levels showing beneath Speech/Music selection

A previous Speech transition could finish after another language was selected,
showing its levels and marking the new source choice ready. Source selection now
sets an explicit pending state that hides deck sections regardless of late display
updates. Each Speech transition has an ownership token checked after its awaited
phases; superseded work cannot expose levels, mark the source ready, dismiss a
newer loader, or schedule resume/onboarding surfaces.

The browser suite now starts Speech with a deferred structure load, chooses
another language, then releases the older request. It verifies that the source
choices remain visible and Learn/Practice/Extra sections remain hidden on both
mobile and desktop, including after forced stale display updates. The 135-test
suite and expanded browser checks passed. The fix remains local and undeployed.


## Follow-up: sign-in shell and repeated logout/login

Slow loading of the real Clerk widget put the status below the card and moved
Guest by approximately 100 pixels when the widget arrived. The shell now lays out
its header, provider slot, disclosure, account choices and attribution slot from
the start. Provider markup remains masked until its controls have loaded their
styles and completed layout. Both mobile and desktop measurements now show zero
movement of the header, Guest, disclosure and account links.

Logout raises a cover before its first asynchronous operation and suppresses
intermediate signed-out callbacks until reload. The first language picker after
login is prepared before the next paint instead of appearing after a 150 ms gap.
`tests/app/auth_layout_browser.cjs` checks delayed widget markup/styles and two
logout/login cycles on both mobile and desktop, including transition stacking and
no bare-setup frame after login. Provider loading and loaded screenshots were also
checked with the real unauthenticated Clerk widget; no real account was used.
