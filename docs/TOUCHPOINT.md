# TOUCHPOINT — touch interaction audit

11 October 2026. Spanish and Portuguese first. Josh narrowed this task to a
code-led gesture audit and approved the targeted fixes below; two-device
testing is deferred because cross-device saving has worked well in his use.

## Automated evidence

The original handler was exercised with synthetic touch events in Node:

- A 13px back-face drag graded without displaying an indicator (50px threshold).
- A 60px horizontal movement followed by 140px vertical movement still graded
  because the earlier indicator stayed visible.
- A 40px vertical movement cycled examples without identifying scrollports.
- No grading touchcancel handler existed.
- Non-touch grading dismissed the first-swipe hint despite a gesture parameter.
- Both touchend and click could flip a card. Double delivery was a risk, not a
  physically observed failure.
- Starts over buttons/onclick surfaces were excluded completely, reducing the
  usable grading area on a busy back. Josh independently reported this friction.

## Implemented behaviour

- One 50 CSS-pixel distance threshold, independent of speed, for indicators and
  grading in either direction. Drag feedback retains the existing appearance.
- Direction locks after 10px with a 1.15 directional lead. A vertical gesture
  cannot become grading; horizontal commitment also requires a horizontal final
  position, using the release coordinates rather than stale move coordinates.
- Actual overflow scrollports retain native vertical scrolling. Vertical cycling
  remains outside them on non-control areas of the back.
- Button taps retain their existing click/activation handlers. Deliberate
  horizontal drags can start over them; capture-phase release handling prevents
  a consumed drag from also activating an inline touchend action. Moved gestures
  suppress their subsequent synthetic click. The set scrubber retains its own
  drag navigation.
- Cancelled/multiple-touch gestures reset. The existing Spotify hold timer is
  cancelled on movement so a button-started drag cannot trigger a delayed hold.
- Grading is guarded through animation and asynchronous phrase-child loading;
  the guard releases on completion or failure. Keyboard/button grading keeps the
  same semantics but cannot grade twice during the transition.
- Existing click handlers are the sole owner of stationary taps and flips.
  Keyboard clicks and identifiable mouse clicks are not suppressed.
- The first-swipe hint is learned only after accepted touch grading.

No progress schema, identity, merge rules, scheduling rules, layout, button
positions or visual controls changed. Existing unrelated CSS/main/roadmap/pipeline
edits were preserved. SEAM was notified before handler changes.

## Validation and staging

Focused tests exercise the actual touch arbiter, both directions and feedback,
sub-threshold drags, final release coordinates, diagonal movements, axis locking,
scrollport ownership, cycling, controls, interrupted gestures, multiple touches,
scrubber exclusion, idempotent setup, busy transitions and click suppression.
Integration tests exercise duplicate grade rejection, hint ownership and guard
release after async errors. Existing onboarding and local resume tests also pass.

Full app suite and staging browser review: pending publication.

## Physical-device evidence and limits

No physical phones were operated in this task. Device models, OS versions and
phone browser versions: unavailable. Actual one-handed feel, native touch scroll
momentum, platform click delivery and edge/browser navigation gestures remain
unverified. Automated tests do not establish those outcomes.

Josh's report: overall interaction works, but buttons sometimes make left/right
swiping harder. Cross-device saved progress has worked in his experience; no sync
failure is claimed. Two-real-device progress and resume checks are deferred at his
request, rather than marked passed. Local resume regression tests are separate
automated evidence.

Production promotion requires Josh's explicit approval; none was performed.
