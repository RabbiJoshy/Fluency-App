-- Live playlist lyrics and the deck built from them. One row per Spotify
-- track so a 200-song import does not hit D1's bind-size ceiling, plus one
-- deck row the study client reloads by user + language.
CREATE TABLE IF NOT EXISTS playlist_live_tracks (
  user_id        TEXT NOT NULL,
  language       TEXT NOT NULL,
  playlist_id    TEXT NOT NULL,
  spotify_id     TEXT NOT NULL,
  title          TEXT NOT NULL DEFAULT '',
  artist         TEXT NOT NULL DEFAULT '',
  album          TEXT NOT NULL DEFAULT '',
  duration_ms    INTEGER,
  status         TEXT NOT NULL DEFAULT '',
  plain_lyrics   TEXT NOT NULL DEFAULT '',
  synced_lyrics  TEXT NOT NULL DEFAULT '',
  lrclib_id      TEXT,
  updated_at     TEXT NOT NULL DEFAULT '',
  PRIMARY KEY (user_id, language, playlist_id, spotify_id)
);

CREATE INDEX IF NOT EXISTS idx_playlist_live_tracks_playlist
  ON playlist_live_tracks(user_id, language, playlist_id);

CREATE TABLE IF NOT EXISTS playlist_live_decks (
  user_id             TEXT NOT NULL,
  language            TEXT NOT NULL,
  playlist_id         TEXT NOT NULL,
  playlist_name       TEXT NOT NULL DEFAULT '',
  deck_json           TEXT NOT NULL,
  track_count         INTEGER NOT NULL DEFAULT 0,
  lyrics_track_count  INTEGER NOT NULL DEFAULT 0,
  matched_count       INTEGER NOT NULL DEFAULT 0,
  token_count         INTEGER NOT NULL DEFAULT 0,
  updated_at          TEXT NOT NULL DEFAULT '',
  PRIMARY KEY (user_id, language, playlist_id)
);

CREATE INDEX IF NOT EXISTS idx_playlist_live_decks_user_lang
  ON playlist_live_decks(user_id, language, updated_at);
