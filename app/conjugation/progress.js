/* Conjugation progress — local-first, per account and per language.
 *
 * A conjugation cell is not an observed surface form, so it cannot share the
 * vocabulary system's card_id = f(language, surface_key). This store runs
 * parallel to it: one record per form, keyed `verb|tenseId|person`, which the
 * deck builder keeps stable (headwords are unique within a deck). Pattern
 * (lesson) progress is folded from those records at read time, never stored.
 *
 * Three things are kept, each under its own key so one can be cleared or
 * corrupted without touching the others:
 *   conj_progress_v1_<account>_<lang>   form -> record
 *   conj_session_v1_<account>_<lang>    the drill in flight, for resuming
 *   conj_settings_v1_<lang>             the Set up choices (device-wide)
 *
 * Scheduling is a plain Leitner ladder. A miss drops the form to the bottom
 * and makes it due at once; a hit moves it up a box and pushes it out.
 * Storage is best-effort: a private window or full quota degrades to an
 * in-memory store for the page's life rather than an error.
 */
(function (root) {
  'use strict';

  var MINUTE = 60 * 1000;
  var DAY = 24 * 60 * MINUTE;
  // Box n waits INTERVALS[n] after a hit. Box 0 is "just missed".
  var INTERVALS = [0, 10 * MINUTE, DAY, 3 * DAY, 7 * DAY, 21 * DAY, 60 * DAY];
  var MAX_BOX = INTERVALS.length - 1;
  var KNOWN_BOX = 3;   // survived a hit a day or more after the last one

  var memory = {};

  function storage() {
    try { return root.localStorage || null; } catch (error) { return null; }
  }

  function read(key) {
    var store = storage();
    var raw = null;
    try { raw = store ? store.getItem(key) : null; } catch (error) { raw = null; }
    if (raw == null) raw = Object.prototype.hasOwnProperty.call(memory, key) ? memory[key] : null;
    if (raw == null) return null;
    try { return JSON.parse(raw); } catch (error) { return null; }
  }

  function write(key, value) {
    var raw = JSON.stringify(value);
    memory[key] = raw;
    var store = storage();
    try { if (store) store.setItem(key, raw); } catch (error) { /* memory copy stands */ }
  }

  function remove(key) {
    delete memory[key];
    var store = storage();
    try { if (store) store.removeItem(key); } catch (error) { /* nothing to do */ }
  }

  /* The study app's signed-in user, so two people on one device keep
   * separate ladders. Guests share one. */
  function account() {
    var user = read('flashcardUser');
    var initials = user && !user.isGuest && user.initials;
    return initials ? String(initials).replace(/[^\w-]/g, '') || 'guest' : 'guest';
  }

  function progressKey(lang) { return 'conj_progress_v1_' + account() + '_' + lang; }
  function sessionKey(lang) { return 'conj_session_v1_' + account() + '_' + lang; }
  function settingsKey(lang) { return 'conj_settings_v1_' + lang; }

  function formKey(verbHead, tenseId, person) {
    return verbHead + '|' + tenseId + '|' + person;
  }

  function load(lang) {
    var stored = read(progressKey(lang));
    return stored && stored.forms && typeof stored.forms === 'object'
      ? stored : { version: 1, forms: {} };
  }

  function save(lang, progress) {
    progress.updatedAt = Date.now();
    write(progressKey(lang), progress);
  }

  /* Apply one answer to a record and return it. Pure apart from `now`. */
  function grade(record, correct, now) {
    var next = record ? {
      box: record.box | 0, seen: record.seen | 0, right: record.right | 0,
      wrong: record.wrong | 0, due: record.due || 0, last: record.last || 0
    } : { box: 0, seen: 0, right: 0, wrong: 0, due: 0, last: 0 };
    next.seen += 1;
    next.last = now;
    if (correct) {
      next.right += 1;
      next.box = Math.min(MAX_BOX, next.box + 1);
    } else {
      next.wrong += 1;
      next.box = 0;
    }
    next.due = now + INTERVALS[next.box];
    return next;
  }

  function record(lang, key, correct, now) {
    var progress = load(lang);
    progress.forms[key] = grade(progress.forms[key], correct, now || Date.now());
    save(lang, progress);
    return progress.forms[key];
  }

  /* new: never answered. missed: last answer wrong. learning: climbing.
   * known: reached KNOWN_BOX. `due` is orthogonal: anything answered whose
   * wait has run out. */
  function status(rec, now) {
    if (!rec || !rec.seen) return { state: 'new', due: true };
    var state = rec.box === 0 ? 'missed' : rec.box >= KNOWN_BOX ? 'known' : 'learning';
    return { state: state, due: (rec.due || 0) <= now };
  }

  /* Counts over a list of form keys. */
  function summarise(progress, keys, now) {
    var out = { total: keys.length, new: 0, missed: 0, learning: 0, known: 0, due: 0 };
    keys.forEach(function (key) {
      var s = status(progress.forms[key], now);
      out[s.state] += 1;
      // Missed forms are always due; `due` counts the ones coming back on schedule.
      if (s.due && (s.state === 'learning' || s.state === 'known')) out.due += 1;
    });
    return out;
  }

  /* Rank for "weakest first": missed, then due by how overdue, then new,
   * then the rest by when they come due. Lower sorts first. */
  function priority(rec, now) {
    var s = status(rec, now);
    if (s.state === 'missed') return [0, rec.due || 0];
    if (s.state === 'new') return [2, 0];
    if (s.due) return [1, rec.due];
    return [3, rec.due];
  }

  function resetLanguage(lang) {
    remove(progressKey(lang));
    remove(sessionKey(lang));
  }

  function loadSession(lang) {
    var session = read(sessionKey(lang));
    if (!session || !Array.isArray(session.keys) || !session.keys.length) return null;
    return session;
  }

  function saveSession(lang, session) {
    if (!session || !session.keys || !session.keys.length) { remove(sessionKey(lang)); return; }
    session.updatedAt = Date.now();
    write(sessionKey(lang), session);
  }

  function clearSession(lang) { remove(sessionKey(lang)); }

  function loadSettings(lang) { return read(settingsKey(lang)); }
  function saveSettings(lang, settings) { write(settingsKey(lang), settings); }

  root.ConjugationProgress = {
    INTERVALS: INTERVALS,
    KNOWN_BOX: KNOWN_BOX,
    account: account,
    formKey: formKey,
    load: load,
    save: save,
    grade: grade,
    record: record,
    status: status,
    summarise: summarise,
    priority: priority,
    resetLanguage: resetLanguage,
    loadSession: loadSession,
    saveSession: saveSession,
    clearSession: clearSession,
    loadSettings: loadSettings,
    saveSettings: saveSettings
  };
})(typeof window !== 'undefined' ? window : globalThis);
