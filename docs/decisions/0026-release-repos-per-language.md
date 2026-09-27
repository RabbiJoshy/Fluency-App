# Decision 0026 — One release site per language (DRAFT)

**Status:** Draft, 2026-09-27. **Proposed, not decided.** Joshua decides. The
steps that create repositories or turn on Pages are his; a session can do the
rest.

## Problem

Every release lives in one repository, `RabbiJoshy/Fluency-Releases`, served as
one GitHub Pages site. Measured from its tree on 2026-09-27:

| Folder | Size | Referenced by `app/config` or `app/js` |
|---|---|---|
| `es/` | 709 MB | `es-speech-v15-mend-10000x10` (356 MB), `v12-6000x10-conj` |
| `pt/` | 690 MB | `pt-speech-v15-mend-10000x10` (345 MB), `v12-6000x10-conj` |
| `lyrics/` | 678 MB | `all-artists-v19`, `bad-bunny-v19`, `test-playlist-v19`, `all-artists-v18`, `all-artists-v7-native-20260825b` |
| `cs/` | 551 MB | `cs-speech-v15-mend-10000x10` (280 MB), `v12-4000x10-conj` |
| `fi/` | 34 MB | `fi-speech-v1-2000x5-3-candidate` |
| `fr/` | 3 MB | both releases |
| **Total** | **2.67 GB** | |

Unreferenced: the three non-MEND `v15-10000x10` speech releases (967 MB), and
`lyrics-{bad-bunny,rosalia,young-miko}-v18` and `lyrics-test-playlist-v16`
(144 MB).

What that costs:

1. **Every publish rebuilds everything.** A git push sends only the changed
   files, but the Pages build re-packages and re-uploads the whole 2.67 GB site.
   The build has grown from 1m05s (2026-09-25) to 2m05s–2m35s (2026-09-27).
   Publishing a lyrics fix redeploys Spanish, Portuguese and Czech speech.
   `docs/ui/UI_WORK_ORDERS.md` rule 6 measured the same effect on the app site:
   pruning 7.2 GB to 1.8 GB cut a build from 5m05s to 1m35s.
2. **It is past GitHub's limit.** Pages documents a 1 GB limit for a published
   site; this one is 2.67 GB. It still builds, but the limit is GitHub's to
   enforce whenever it chooses.
3. **Concurrent sessions collide.** A lyrics session and a speech session
   publishing at once race for one branch, and whichever pushes second must
   pull about a gigabyte of unrelated changes first.
4. **History only grows.** Each 10k speech release adds about 350 MB of history
   that is never pruned (GitHub's guidance is under 1 GB per repository, and
   strongly under 5 GB).

Pruning alone gets to about 1.55 GB, which is still over the limit and still
rebuilds every language on every publish.

## Proposal

**One repository and Pages site per first path segment**, named by
convention, so a new language needs a new repository and no code change
(Invariant 5):

```
releases/<segment>/…  →  https://rabbijoshy.github.io/Fluency-Releases-<segment>/…
```

This gives `Fluency-Releases-es`, `-pt`, `-cs`, `-fi`, `-fr` and `-lyrics`.
The largest is lyrics at about 540 MB once the unreferenced releases go,
which leaves room for one new release beside the current one before the old one
is pruned.

The app is still served from `rabbijoshy.github.io`, so there is no CORS or
service-worker scope change; only the path prefix moves.

### Rules for each release repository

- **Holds only what config references, plus one rollback per mode.** A
  publish prunes the rest in the same commit.
- **One commit on `gh-pages`, force-pushed.** These repositories hold generated output; the
  workspace is the source of truth (UI_WORK_ORDERS rule 6). Publishing replaces
  the branch with a single commit of the current tree, so the repository stays
  the size of the site. This is the one place force-pushing is the convention.
- **Written only by `scripts/publish_release.py`** (below), never by hand, the
  same way `gh-pages` of the app is written only by its workflow.

## Work

Step 1 needs Josh: a session cannot create repositories. Everything else a
session can do.

1. **Create the repositories** `Fluency-Releases-{es,pt,cs,fi,fr,lyrics}`
   (public). *Done 2026-09-27 for es, pt, cs, fr and lyrics; `-fi` does not
   exist yet.* Each publishes from a `gh-pages` branch: pushing that branch
   turned Pages on without a settings change, and a session can do it. A
   README on `main` (fr, lyrics) is harmless and unused.
2. **`scripts/publish_release.py --segment es --release-dir <workspace path>`**:
   sparse-clone the segment's repository, copy the release in, prune releases
   no longer referenced by `app/config/config.json` or `app/config/artists.json`
   (keeping one rollback per mode), write a single commit, force-push, then wait
   for the Pages build. Push to `gh-pages`, never `main`. Replace the hard-coded `/private/tmp/fluency-releases`
   in `scripts/run_v12_production.py` and `scripts/mend_local.py` with it.
3. **Seed the new repositories** from the current `Fluency-Releases` tree, keeping
   only referenced releases: roughly es 357 MB, pt 346 MB, cs 280 MB,
   lyrics 540 MB, fi 34 MB, fr 3 MB.
4. **Point the app at them.** `RELEASE_BASE_URL` in `app/js/release-host.js`
   becomes a function of the first segment; extend `tests/app/test_release_host.py`
   with one case per segment. Deploy through `main`.
5. **Retire the combined site** a week later, once installed apps have picked
   up the new service worker: prune `Fluency-Releases` to a README that points
   to the new sites.
6. **Update `CLAUDE.md`** ("Releases are not on `gh-pages`") and the release
   runbooks to name `publish_release.py`.

## Past this

If one segment outgrows 1 GB (lyrics is the likeliest), split it by release
or move release hosting to object storage with a CDN (Cloudflare R2 serves
egress free). `release-host.js` is still the only file that would change.
