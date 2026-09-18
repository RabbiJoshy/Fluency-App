# SETLIST — live playlist study

Repo `Fluency-Next`. This is a **product/UI job**, not a speech-pipeline chat. Do not harvest, WSD, compose, or activate a lyrics release. Skim `CHAT_ROADMAP.md` through SCAR so the study UI still matches display-v4 / v12 speech. Then only this file.

Published artist catalogs (Bad Bunny, Rosalía, …) and lyrics WSD (**VERSE**, still parked) are a different path. Do not merge them into this one.

Paste:

> This chat is **SETLIST**. Read `CHAT_ROADMAP.md` through SCAR, then only `docs/runbooks/live-playlist.md`. Finish the production live-playlist path: Spotify playlist → lyrics → Fluency persist → study deck. Do not harvest. Do not WSD. Do not merge Live playlist with “Match a Spotify playlist”.

---

## What this work is

Joshua wants **Music & lyrics** to work from a playlist he is listening to *now*, without waiting for a harvested artist release.

End-to-end:

1. Learner picks **Live playlist** (not “Choose artists or songs”, not “Match a Spotify playlist”).
2. Connects Spotify, picks a **playlist they created**.
3. Sees a **spinner and a percent**, and each song **land in the list** as lyrics resolve.
4. Lyrics persist to **Fluency’s server** (named user) — not IndexedDB-only.
5. Fluency **builds a study deck** from those lyrics and **opens it in place**.

Card identity stays `language + surface`. No sense tagging on this path.

---

## The three music entries (do not collapse)

`showArtistPicker` in `app/js/main.js` has three rows. They stay three.

| Entry | What it is |
|---|---|
| Choose artists or songs | Published lyrics catalog. Existing artist mode. |
| Match a Spotify playlist | Filter that catalog to tracks already in Fluency. Needs a published library. |
| **Live playlist** | This job. Look lyrics up now. Naive deck. No WSD. |

Live must work even when no music collection is published for the language (it overlays the **speech** inventory). Matching must stay disabled when there is no catalog.

---

## How the live deck is allowed to be naive

Joshua asked for the naive version first, then to treat it as the real production experience.

- Tokenise lyric lines in the browser (`naiveLyricTokens` in `app/js/playlist-live.js`). Unicode letters/numbers, strip `[...]` markers.
- Keep a token only if it already exists on the **speech** inventory for that language.
- Rank cards by how often the token appears in this playlist.
- Speech sense overlay: keep **common and uncommon**, drop **rare** (`share >= 0.05`; drop `isRareSense` / prominence `rare`).
- Song lines are examples marked **`unassigned: true`**. Do not invent WSD labels.
- Open study with `history.replaceState` (`playlistLive=1`) and the existing speech language tab. Do not full-page reload if that drops the deck.

This is not lyrics WSD v16. VERSE/GRAFT stay parked.

---

## Lyrics source

There is no simple official lyrics API. Genius scrape, `spotify-lyrics-scraper`, and dump downloads were rejected as too slow, unofficial, or huge (the 43 GiB dump is irrelevant: every user has different songs, so cache-from-dump does not help).

**LRCLIB** is the lookup (`https://lrclib.net/api/search`, 6 concurrent, `LOOKUP_CONCURRENCY` in `app/js/spotify-playlist-import.js`). Probe playlist used in this work: `0ubVKl2OeeqSa5C0I3zbq7`. Coverage will be incomplete; instrumentals and misses are first-class statuses, not failures of the whole import.

Do not switch provider unless Joshua asks. Speed work is parallelism and UI progress, not a new corpus.

---

## Persistence (this was the point)

Joshua rejected “it lives in IndexedDB on this phone.”

| Who | Where |
|---|---|
| Named user (JST, initials, not guest) | Cloudflare Worker `https://fluency-api.rabbijoshy.workers.dev` — actions `savePlaylistLiveTracks`, `savePlaylistLiveDeck`, `loadPlaylistLiveDeck`; capability `playlistLive`. Worker code is in the **old** repo: `../Fluency/backend/worker/src/index.js` (migration `0005_playlist_live.sql`). |
| Guest | Local deck only (`IndexedDB` `fluency-playlist-lyrics`, deck id `live`). |
| `fluency dev` | Same POST body also dumped to `<workspace>/raw/playlists/<user>/<lang>/<playlist-id>/` via `src/fluency/lyrics/playlist_live.py`. That is a disk dump for Joshua, not the production store. |

Client: `postPlaylistLive` in `app/js/spotify-playlist-import.js`. Google-script-shaped JSON (`action`, `success`). `GOOGLE_SCRIPT_URL` / `progressSyncUrl` already points at the worker.

Do not rebuild harvest/WSD “so it has somewhere to go.” The worker is the somewhere.

---

## Spotify (blocker that looked like auth)

`GET /me/playlists` still lists playlists. **Development-mode apps** (this one: client id in `app/config/config.json`) cannot read songs from `GET /playlists/{id}/tracks` after Spotify’s **February 2026** Web API change. That endpoint 403s even on playlists you own. Reconnect / extra scopes do not fix it.

Replacement: `GET /playlists/{id}/items`. Response row field is `item` (old `track` still parsed as fallback). Contents only for playlists the user **owns or collaborates on**. Mixes, Daily Mix, Discover Weekly, and followed editorial lists stay visible but unreadable — grey them out, do not pretend reconnect will open them.

Shipped in `app/js/spotify.js` (commit `6007185`, asset `20260918l`, cache `flashcards-v467`). Live GitHub Pages often lags a few minutes; confirm `/items` is actually in the served `spotify.js` before debugging auth again.

---

## UX that already had to be true

The import is the product, not a fire-and-forget fetch:

- Spinner + percent while lyrics resolve.
- Each song named as it lands (lyrics / instrumental / no lyrics / error / cached / saving).
- Then save to Fluency, then open the deck.
- Playlist tap must not ghost-click Cancel or the backdrop (dismiss lock). A 401/403 on track fetch must **not** `spotifyLogin` and bounce mobile to the main menu (`allowReauth: false` on track pages).

Live is enabled when speech exists for the language, even if published lyrics are empty.

---

## Files

| Path | Role |
|---|---|
| `app/js/spotify-playlist-import.js` | Modal, LRCLIB, progress UI, POST tracks/deck, open study |
| `app/js/playlist-live.js` | Tokens, overlay, IDB deck, server save/load |
| `app/js/spotify.js` | PKCE, `/me/playlists`, `/playlists/{id}/items` |
| `app/js/main.js` | Three music entries; `playlistLive=1` boot |
| `app/js/vocab.js` | `applyPlaylistLiveVocabulary` when live is active |
| `src/fluency/lyrics/playlist_live.py` | Local `fluency dev` dump |
| `../Fluency/backend/worker/src/index.js` | Production D1 persist |
| `tests/app/test_product_shell.py` | Shell contracts for the importer |
| `tests/lyrics/test_playlist_live.py` | Local dump |

UI edits under `app/` still deploy to **gh-pages** (root + `app/` mirror) at the end of the turn.

---

## Done in this campaign

- Chose LRCLIB; 6-wide lookup; progress UI with songs landing.
- Naive speech-overlay deck, unassigned lyric examples, in-place open.
- Worker + local dump persistence; named user vs guest.
- Three music modes left distinct; Live not blocked on a published catalog.
- Playlist-tap crash and stale-Pages 403s diagnosed.
- Spotify `/tracks` → `/items` for Feb 2026 development-mode API.

## Not done until Joshua can do this on the live site

1. Hard-refresh Fluency. Pick **Live playlist**. Pick a **homemade** Spotify playlist (not a Mix).
2. Watch percent + song names. Confirm lyrics land.
3. Confirm the deck opens and speech cards show **his song lines**.
4. Sign in as JST (or initials) and confirm a reload still has the deck (`loadPlaylistLiveDeck`).
5. Confirm “Match a Spotify playlist” is still the catalog filter, unchanged.

If step 1 still 403s on a playlist he owns, the served JS is stale or `/items` itself failed — check the live `spotify.js` for `/items`, then the raw Spotify error body. Do not reopen lyrics-provider research or WSD.
