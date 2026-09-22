/* Conjugation mode — standalone prototype.
 *
 * Deliberately has no progress model: nothing is scored, stored or scheduled.
 * The only job here is the selection layer — pick tenses, pick a slice of
 * verbs, and see exactly which cards that produces — plus a keyboard/swipe
 * drill and a reference table.
 *
 * Decks are emitted by scripts/build_conjugation_drill.py and register
 * themselves by calling window.registerConjugationDeck(deck).
 */
(function () {
  'use strict';

  var decks = {};
  var deck = null;

  var state = {
    tenses: {},      // tenseId -> true
    persons: {},     // person  -> true
    types: { 0: true, 1: true, 2: true, 3: true, 4: false },
    scope: 50,       // percentile of the ranked verb list
    reverse: false,  // prompt with the English meaning instead of the infinitive
    patterns: {},    // stem delta -> true
    coverage: 'all', // 'all' every card, 'one' one card per lesson
    speak: true,     // read the answer out loud on reveal
    easy: false      // tint the prompt by what this card does, and name the family
  };

  // The study app names languages ('spanish'); the deck codes them ('es').
  // speech.js reads window.selectedLanguage to pick a locale.
  var SPEECH_LANGUAGE = { es: 'spanish', pt: 'portuguese', fr: 'french', cs: 'czech' };

  var queue = [];
  var position = 0;
  var revealed = false;
  var soloVerb = null;   // set by ?verb=, cleared when the selection changes
  var expandedMoods = {};  // mood label -> the rarer tenses are showing

  var CODE_ORDER = ['0', '1', '2', '3', '4'];
  var OPAQUE = '*';

  window.registerConjugationDeck = function (payload) {
    decks[payload.language] = payload;
  };

  /* ── helpers ────────────────────────────────────────── */

  function $(id) { return document.getElementById(id); }

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text != null) node.textContent = text;
    return node;
  }

  function tenseById(id) {
    return deck.tenses.filter(function (t) { return t.id === id; })[0];
  }

  function selectedTenseIds() {
    return deck.tenses.map(function (t) { return t.id; })
      .filter(function (id) { return state.tenses[id]; });
  }

  function selectedPersons() {
    return deck.person_order.filter(function (p) { return state.persons[p]; });
  }

  function tenseLabel(tense) { return tense.mood + ' · ' + tense.tense; }

  function personLabel(person) { return deck.pronouns[person] || person; }

  /* The verb list the scope slider admits. Verbs whose infinitive never
   * appeared in the frequency inventory have no rank; they sort last and are
   * only included once the slider reaches the end. */
  function verbsInScope() {
    var ranked = deck.verbs.filter(function (v) { return v.n != null; });
    if (state.scope >= 100) return deck.verbs.slice();
    return ranked.slice(0, Math.max(1, Math.round(ranked.length * state.scope / 100)));
  }

  /* A verb's difficulty is relative to the current selection: the worst code
   * across the selected tenses and persons only. */
  function verbCode(verb, tenseIds, persons) {
    var worst = -1;
    var sawUnknown = false;
    for (var i = 0; i < tenseIds.length; i++) {
      var paradigm = verb.p[tenseIds[i]];
      if (!paradigm) continue;
      var order = tenseById(tenseIds[i]).persons;
      for (var j = 0; j < order.length; j++) {
        if (persons.indexOf(order[j]) === -1) continue;
        var code = paradigm.c.charAt(j);
        if (code === '-') continue;
        // Unclassified is an absence of evidence, not evidence of
        // irregularity, so it never raises a verb's type on its own.
        if (code === '4') { sawUnknown = true; continue; }
        var value = parseInt(code, 10);
        if (value > worst) worst = value;
      }
    }
    if (worst < 0 && sawUnknown) return 4;
    return worst;
  }

  function currentSelection() {
    var tenseIds = selectedTenseIds();
    var persons = selectedPersons();
    var byType = { 0: 0, 1: 0, 2: 0, 3: 0, 4: 0 };
    var chosen = [];
    var pool = soloVerb ? [soloVerb] : verbsInScope();

    pool.forEach(function (verb) {
      var code = verbCode(verb, tenseIds, persons);
      if (code < 0) return;
      byType[code] += 1;
      if (state.types[code]) chosen.push(verb);
    });

    return { tenseIds: tenseIds, persons: persons, verbs: chosen, byType: byType };
  }

  /* Reads a form out loud through the study app's own voice engine. If that
   * module has not loaded, this is silently a no-op rather than an error. */
  function speak(text) {
    if (!state.speak || !text) return;
    if (typeof window.speakWord !== 'function') return;
    window.speakWord(text);
  }

  /* Split a form into the stem and the ending the lesson turns on, so the
   * ending can be coloured. Returns null when the split would not be honest:
   * compound tenses, off-model forms, and anything whose ending the model
   * could not identify. */
  function splitEnding(form, lesson) {
    if (!lesson || !form) return null;
    var ending = lesson.e;
    if (!ending || ending === OPAQUE || ending.charAt(0) === '\u00b7') return null;
    if (form.length <= ending.length) return null;
    if (form.slice(-ending.length) !== ending) return null;
    return { stem: form.slice(0, form.length - ending.length), ending: ending };
  }

  function paintForm(node, form, lesson, code) {
    node.innerHTML = '';
    var split = splitEnding(form, lesson);
    if (!split) {
      var plain = el('span', null, form);
      if (code && code !== '0' && code !== '-') plain.style.color = 'var(--c' + code + ')';
      node.appendChild(plain);
      return;
    }
    node.appendChild(el('span', 'form-stem', split.stem));
    var tail = el('span', 'form-ending', split.ending);
    tail.style.setProperty('--ending-colour', 'var(--c' + (code === '-' ? '4' : code) + ')');
    node.appendChild(tail);
  }

  /* A verb's pattern family: the alternation it is known for, across every
   * tense. Deliberately not this card's delta — naming that would say
   * whether the stem changes *here*, which is the question. Saying "o → ue
   * verb" on `encontramos` leaves you to know that nosotros sits outside
   * the stress pattern. */
  var verbFamily = {};
  var familyMembers = {};

  function computeFamilies() {
    verbFamily = {};
    var opening = deck.tenses.filter(function (t) {
      return !t.compound && t.mood_order === 1 && t.order === 1;
    })[0];

    function tally(verb, onlyTense) {
      var counts = {};
      Object.keys(verb.p).forEach(function (tenseId) {
        if (onlyTense && tenseId !== onlyTense) return;
        var paradigm = verb.p[tenseId];
        if (!paradigm.l) return;
        paradigm.l.forEach(function (id) {
          if (id === null || id === undefined) return;
          var delta = deck.lessons[id].d;
          if (!delta) return;            // the plain pattern names nothing
          counts[delta] = (counts[delta] || 0) + 1;
        });
      });
      var best = null;
      Object.keys(counts).forEach(function (delta) {
        if (delta === OPAQUE) return;    // suppletion is a last resort
        if (!best || counts[delta] > counts[best]) best = delta;
      });
      if (!best && counts[OPAQUE]) best = OPAQUE;
      return best;
    }

    familyMembers = {};
    deck.verbs.forEach(function (verb) {
      // The present is how a learner identifies a verb. Counting every tense
      // instead makes `tener` an "en → uv verb", because the tuv- stem spans
      // the preterite and two subjunctives — true, but not how anyone thinks
      // of it. Fall back to the whole paradigm only when the present is flat.
      var best = (opening && tally(verb, opening.id)) || tally(verb, null);
      verbFamily[verb.h] = best === undefined ? null : best;
      if (best && best !== OPAQUE) {
        // deck.verbs is already in rank order, so the first members added are
        // the ones a learner is likeliest to recognise. The builder's own
        // example list is alphabetical, which offers `advertir` for the
        // family everyone knows as `pensar`.
        var members = familyMembers[best] || (familyMembers[best] = []);
        if (members.length < 8) members.push(verb.h);
      }
    });
  }

  /* Name a family by the verbs in it. "like pensar, querer" is what a person
   * would say; the machine-readable delta stays on the answer side. */
  function familyPhrase(delta, exclude) {
    var members = (familyMembers[delta] || []).filter(function (h) {
      return h !== exclude;
    });
    if (!members.length) return patternLabel({ d: delta }) + ' verb';
    return 'like ' + members.slice(0, 2).join(', ');
  }

  function lessonAt(paradigm, index) {
    var id = paradigm.l && paradigm.l[index];
    return (id === null || id === undefined) ? null : deck.lessons[id];
  }

  /* One enumeration, used both to count the selection and to build the
   * queue, so the number on the Choose screen is the number you drill. */
  function enumerateCards(selection) {
    var cards = [];
    selection.verbs.forEach(function (verb) {
      selection.tenseIds.forEach(function (tenseId) {
        var paradigm = verb.p[tenseId];
        if (!paradigm) return;
        var tense = tenseById(tenseId);
        tense.persons.forEach(function (person, index) {
          if (selection.persons.indexOf(person) === -1) return;
          if (!paradigm.f[index]) return;
          var lesson = lessonAt(paradigm, index);
          var delta = lesson ? lesson.d : null;
          if (delta !== null && !state.patterns[delta]) return;
          cards.push({
            verb: verb,
            tense: tense,
            person: person,
            form: paradigm.f[index],
            code: paradigm.c.charAt(index),
            lesson: lesson
          });
        });
      });
    });
    return cards;
  }

  function shuffle(cards) {
    for (var i = cards.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var swap = cards[i]; cards[i] = cards[j]; cards[j] = swap;
    }
    return cards;
  }

  /* In coverage mode the queue holds one card per lesson. Shuffling first
   * means the surviving card is a random verb from that lesson, so you are
   * not always taught `o>ue` by the same verb. */
  function buildQueue(selection) {
    var cards = shuffle(enumerateCards(selection));
    if (state.coverage !== 'one') return cards;
    var seen = {};
    return cards.filter(function (card) {
      var key = card.lesson ? String(card.lesson.d) + '|' + card.tense.id + '|' + card.person
        : 'x|' + card.tense.id + '|' + card.person;
      if (seen[key]) return false;
      seen[key] = true;
      return true;
    });
  }

  /* ── setup screen ───────────────────────────────────── */

  function renderDeckPicker() {
    var select = $('deck');
    select.innerHTML = '';
    Object.keys(decks).forEach(function (code) {
      var option = el('option', null, code.toUpperCase() + ' — ' + decks[code].locale);
      option.value = code;
      select.appendChild(option);
    });
    select.value = deck.language;
    select.disabled = Object.keys(decks).length < 2;
    select.onchange = function () { loadDeck(decks[select.value]); };
  }

  /* Moods keep the deck's order, which the builder sets to the order a
   * learner meets them: indicative before subjunctive before imperative,
   * present before preterite, archaic tenses last. Within a mood the rarer
   * tenses stay behind a "more" toggle rather than padding the list. */
  function renderTenses() {
    var host = $('tenses');
    host.innerHTML = '';

    var moods = [];
    deck.tenses.forEach(function (tense) {
      if (moods.indexOf(tense.mood) === -1) moods.push(tense.mood);
    });

    moods.forEach(function (mood) {
      var group = deck.tenses.filter(function (t) { return t.mood === mood; });
      var rare = group.filter(function (t) {
        return !t.common && !state.tenses[t.id];
      });
      var shown = state.expandAll || expandedMoods[mood]
        ? group
        : group.filter(function (t) { return rare.indexOf(t) === -1; });

      var block = el('div', 'mood');
      var head = el('div', 'mood-head');
      head.appendChild(el('span', null, mood));

      var allOn = group.every(function (t) { return state.tenses[t.id]; });
      var toggle = el('button', null, allOn ? 'none' : 'all');
      toggle.onclick = function () {
        group.forEach(function (t) { state.tenses[t.id] = !allOn; });
        if (!allOn) expandedMoods[mood] = true;
        renderTenses();
        refreshSummary();
      };
      head.appendChild(toggle);
      block.appendChild(head);

      var checks = el('div', 'checks');
      shown.forEach(function (tense) {
        var label = el('label', 'check');
        var input = document.createElement('input');
        input.type = 'checkbox';
        input.checked = !!state.tenses[tense.id];
        input.onchange = function () {
          state.tenses[tense.id] = input.checked;
          renderTenses();
          refreshSummary();
        };
        label.appendChild(input);
        label.appendChild(el('span', 'check-name', tense.tense));
        if (tense.compound) label.appendChild(el('span', 'compound-dot'));
        label.appendChild(el('span', 'check-count', tense.persons.length + ' forms'));
        checks.appendChild(label);
      });
      block.appendChild(checks);

      if (rare.length && !expandedMoods[mood]) {
        var more = el('button', 'linkish mood-more',
          '+ ' + rare.length + ' rarer ' + (rare.length === 1 ? 'tense' : 'tenses'));
        more.onclick = function () {
          expandedMoods[mood] = true;
          renderTenses();
        };
        block.appendChild(more);
      }

      host.appendChild(block);
    });
  }

  function renderPersons() {
    var host = $('persons');
    host.innerHTML = '';
    deck.person_order.forEach(function (person) {
      var label = el('label', 'check');
      var input = document.createElement('input');
      input.type = 'checkbox';
      input.checked = !!state.persons[person];
      input.onchange = function () {
        state.persons[person] = input.checked;
        refreshSummary();
      };
      label.appendChild(input);
      label.appendChild(el('span', 'check-name', personLabel(person)));
      host.appendChild(label);
    });
  }

  /* Easy mode gives two cues that do not overlap, so they are one switch
   * rather than a choice: the prompt is tinted by what *this card* does
   * (tener is orange on tengo, green on tenemos), and a line names the
   * family the verb belongs to without saying whether it bites on this
   * person. */
  function renderClue() {
    var host = $('clue');
    host.innerHTML = '';
    var label = el('label', 'check');
    var input = document.createElement('input');
    input.type = 'checkbox';
    input.checked = state.easy;
    input.onchange = function () {
      state.easy = input.checked;
      refreshSummary();
      if (queue.length) renderCard();
    };
    label.appendChild(input);
    label.appendChild(el('span', 'check-name', 'Easy mode'));
    label.appendChild(el('span', 'check-count', 'colour the prompt, name the family'));
    host.appendChild(label);
  }

  function renderDirection() {
    var host = $('direction');
    host.innerHTML = '';
    [
      { value: false, name: 'Show the infinitive', note: 'tener · yo → tengo' },
      { value: true, name: 'Show the meaning', note: 'to have · yo → tengo' }
    ].forEach(function (option) {
      var label = el('label', 'check');
      var input = document.createElement('input');
      input.type = 'radio';
      input.name = 'direction';
      input.checked = state.reverse === option.value;
      input.onchange = function () {
        state.reverse = option.value;
        refreshSummary();
        if (queue.length) renderCard();
      };
      label.appendChild(input);
      label.appendChild(el('span', 'check-name', option.name));
      label.appendChild(el('span', 'check-count', option.note));
      host.appendChild(label);
    });

    var sound = el('label', 'check');
    var box = document.createElement('input');
    box.type = 'checkbox';
    box.checked = state.speak;
    box.onchange = function () { state.speak = box.checked; refreshSummary(); };
    sound.appendChild(box);
    sound.appendChild(el('span', 'check-name', 'Read the answer out loud'));
    sound.appendChild(el('span', 'check-count', 'same voice as the cards'));
    host.appendChild(sound);
  }

  function patternLabel(pattern) {
    if (pattern.d === '') return 'no change · the plain pattern';
    // '*' means the ending did not match the model at all. Those forms do
    // share something — being off-model — so they are not one-offs.
    if (pattern.d === '*') return 'off the model';
    return pattern.d.replace('>', ' \u2192 ').replace(/0/g, '\u2205');
  }

  function renderPatterns() {
    var host = $('patterns');
    host.innerHTML = '';
    deck.patterns.forEach(function (pattern) {
      var label = el('label', 'check');
      var input = document.createElement('input');
      input.type = 'checkbox';
      input.checked = !!state.patterns[pattern.d];
      input.onchange = function () {
        state.patterns[pattern.d] = input.checked;
        refreshSummary();
      };
      label.appendChild(input);
      label.appendChild(el('span', 'check-name', patternLabel(pattern)));
      label.appendChild(el('span', 'check-count',
        pattern.v.slice(0, 2).join(', ') + ' · ' + pattern.n));
      host.appendChild(label);
    });
  }

  function renderCoverage() {
    var host = $('coverage');
    host.innerHTML = '';
    [
      { value: 'all', name: 'Every form', note: 'the full selection' },
      { value: 'one', name: 'One per lesson', note: 'skip what repeats' }
    ].forEach(function (option) {
      var wrap = el('label', 'check');
      var input = document.createElement('input');
      input.type = 'radio';
      input.name = 'coverage';
      input.checked = state.coverage === option.value;
      input.onchange = function () {
        state.coverage = option.value;
        refreshSummary();
      };
      wrap.appendChild(input);
      wrap.appendChild(el('span', 'check-name', option.name));
      wrap.appendChild(el('span', 'check-count', option.note));
      host.appendChild(wrap);
    });
  }

  function renderTypes(byType) {
    var host = $('types');
    host.innerHTML = '';
    CODE_ORDER.forEach(function (code) {
      var count = byType ? byType[code] : 0;
      var label = el('label', 'check' + (count === 0 ? ' is-empty' : ''));
      var input = document.createElement('input');
      input.type = 'checkbox';
      input.checked = !!state.types[code];
      input.onchange = function () {
        state.types[code] = input.checked;
        refreshSummary();
      };
      var swatch = el('span', 'swatch');
      swatch.style.background = 'var(--c' + code + ')';
      label.appendChild(input);
      label.appendChild(swatch);
      label.appendChild(el('span', 'check-name', deck.code_labels[code]));
      label.appendChild(el('span', 'check-count', count + ' verbs'));
      host.appendChild(label);
    });
  }

  /* Each collapsed section states its own selection, so a shut accordion
   * still says what it is doing. */
  function refreshSectionStates(selection) {
    var tenseNames = selection.tenseIds.map(function (id) { return tenseById(id).tense; });
    $('state-tenses').textContent = tenseNames.length === 0 ? 'none'
      : tenseNames.length <= 2 ? tenseNames.join(', ')
      : tenseNames.length + ' tenses';

    var typeNames = CODE_ORDER.filter(function (code) { return state.types[code]; })
      .map(function (code) { return deck.code_labels[code]; });
    $('state-types').textContent = typeNames.length === CODE_ORDER.length ? 'all'
      : typeNames.length === 0 ? 'none'
      : typeNames.length <= 2 ? typeNames.join(', ')
      : typeNames.length + ' types';

    var ranked = deck.verbs.filter(function (v) { return v.n != null; }).length;
    $('state-scope').textContent = state.scope >= 100
      ? 'all ' + deck.verbs.length + ' verbs'
      : 'top ' + Math.round(ranked * state.scope / 100) + ' verbs';

    var persons = selection.persons;
    $('state-persons').textContent = persons.length === deck.person_order.length
      ? 'all ' + persons.length
      : persons.map(personLabel).join(', ') || 'none';

    var on = deck.patterns.filter(function (x) { return state.patterns[x.d]; }).length;
    $('state-patterns').textContent = on === deck.patterns.length ? 'all ' + on
      : on === 0 ? 'none' : on + ' of ' + deck.patterns.length;
    $('state-coverage').textContent =
      state.coverage === 'one' ? 'one per lesson' : 'every form';

    $('state-clue').textContent = state.easy ? 'easy mode' : 'off';

    $('state-prompt').textContent =
      (state.reverse ? 'meaning' : 'infinitive') +
      (state.speak ? ' · spoken' : ' · silent') +
      ' · ' + deck.language.toUpperCase();

    // The advanced group is collapsed by default, so it has to say what is
    // inside it — otherwise a narrowed pattern set looks like a missing deck.
    $('state-advanced').textContent = [
      on === deck.patterns.length ? null : 'patterns narrowed',
      state.coverage === 'one' ? 'one per lesson' : null,
      state.reverse ? 'prompted by meaning' : null
    ].filter(Boolean).join(' · ') || 'defaults';
  }

  function refreshSummary() {
    var selection = currentSelection();
    renderTypes(selection.byType);

    var cards = enumerateCards(selection);
    var lessonKeys = {};
    cards.forEach(function (card) {
      lessonKeys[(card.lesson ? card.lesson.d : 'x') + '|' + card.tense.id + '|' + card.person] = 1;
    });
    var lessonCount = Object.keys(lessonKeys).length;
    var cardCount = state.coverage === 'one' ? lessonCount : cards.length;

    $('sum-cards').textContent = cardCount.toLocaleString();
    $('sum-detail').textContent =
      selection.verbs.length + ' verbs · ' +
      selection.tenseIds.length + ' tenses · ' +
      selection.persons.length + ' persons' +
      (state.coverage === 'one'
        ? ''
        : ' · ' + lessonCount.toLocaleString() + ' distinct lessons');

    $('coverage-hint').textContent = state.coverage === 'one'
      ? 'Your selection holds ' + cards.length.toLocaleString() + ' forms but only ' +
        lessonCount.toLocaleString() + ' distinct lessons. You will be shown each ' +
        'lesson once, by a verb picked at random from the verbs that share it.'
      : 'Every form in the selection, including the ' +
        (cards.length - lessonCount).toLocaleString() +
        ' that repeat a lesson you have already been shown.';

    var bar = $('sum-bar');
    bar.innerHTML = '';
    var total = CODE_ORDER.reduce(function (sum, code) {
      return sum + (state.types[code] ? selection.byType[code] : 0);
    }, 0);
    CODE_ORDER.forEach(function (code) {
      if (!state.types[code] || !selection.byType[code]) return;
      var slice = el('span');
      slice.style.background = 'var(--c' + code + ')';
      slice.style.width = (selection.byType[code] / total * 100) + '%';
      slice.title = selection.byType[code] + ' ' + deck.code_labels[code];
      bar.appendChild(slice);
    });

    $('start').disabled = cardCount === 0;

    var ranked = deck.verbs.filter(function (v) { return v.n != null; }).length;
    $('scope-hint').textContent = state.scope >= 100
      ? 'Includes ' + (deck.verbs.length - ranked) + ' verbs whose infinitive never appeared in the frequency inventory, so they have no rank.'
      : 'Ranked by how often the infinitive appears in the ' +
        deck.language.toUpperCase() + ' speech inventory.';

    refreshSectionStates(selection);
  }

  function renderProvenance() {
    var body = $('provenance-body');
    body.innerHTML = '';
    var list = el('dl');
    function row(term, value) {
      list.appendChild(el('dt', null, term));
      list.appendChild(el('dd', null, value));
    }
    row('Deck', deck.deck_version);
    row('Provider', deck.source.provider);
    row('Snapshot', deck.source.snapshot_id);
    row('Content id', deck.source.content_id);
    row('Provenance', deck.source.provenance_status);
    row('Verbs', String(deck.verbs.length));
    row('Forms', deck.total_forms.toLocaleString());
    row('Unclassified forms', String(deck.unclassified_forms));
    body.appendChild(list);
    body.appendChild(el('p', 'hint',
      'Regularity is derived, not supplied by the source: each ending is compared ' +
      'against the commonest ending observed for verbs of the same class in the same ' +
      'tense and person. Forms with no model are shown as unclassified rather than ' +
      'assumed regular.'));
  }

  /* ── drill screen ───────────────────────────────────── */

  function renderCard() {
    if (!queue.length) {
      $('card').innerHTML = '<p class="empty">No cards in this selection.</p>';
      $('drill-hint').textContent = '';
      return;
    }
    var card = queue[position];
    var meaning = card.verb.t || '';

    $('card-tense').textContent = tenseLabel(card.tense);

    var clue = $('card-clue');
    var verbNode = document.querySelector('.card-verb');
    var clueColour = card.code === '-' ? 'var(--c4)' : 'var(--c' + card.code + ')';
    clue.hidden = true;
    clue.textContent = '';
    verbNode.classList.remove('is-clued');
    verbNode.style.removeProperty('--clue-colour');

    if (state.easy) {
      verbNode.classList.add('is-clued');
      verbNode.style.setProperty('--clue-colour', clueColour);

      var family = verbFamily[card.verb.h];
      clue.textContent = !family ? 'a regular verb'
        : family === OPAQUE ? 'no shared pattern \u00b7 recall it'
        : familyPhrase(family, card.verb.h);
      clue.style.setProperty('--clue-colour', 'var(--ink-3)');
      clue.hidden = false;
    }

    $('card-headword').textContent = state.reverse ? meaning : card.verb.h;
    $('card-translation').textContent = state.reverse
      ? (revealed ? card.verb.h : '')
      : meaning;
    $('card-person').textContent = personLabel(card.person);
    paintForm($('card-form'), card.form, card.lesson, card.code);

    var chips = $('card-chips');
    chips.innerHTML = '';

    var typeChip = el('span', 'chip');
    var swatch = el('span', 'swatch');
    swatch.style.background = 'var(--c' + card.code + ')';
    typeChip.appendChild(swatch);
    typeChip.appendChild(el('span', null,
      card.code === '-' ? 'no form' : deck.code_labels[card.code]));
    chips.appendChild(typeChip);

    if (card.tense.compound) {
      chips.appendChild(el('span', 'chip', 'compound · participle ' + (card.verb.pp || '—')));
    }
    if (card.lesson && card.lesson.d !== '') {
      var others = card.lesson.v.filter(function (h) { return h !== card.verb.h; });
      var lessonChip = el('span', 'chip');
      lessonChip.appendChild(el('span', 'chip-delta', patternLabel({ d: card.lesson.d })));
      if (others.length) {
        lessonChip.appendChild(el('span', null, 'like ' + others.slice(0, 3).join(', ')));
      } else {
        lessonChip.appendChild(el('span', null, 'only this verb'));
      }
      chips.appendChild(lessonChip);
    }
    if (card.verb.r) chips.appendChild(el('span', 'chip', 'reflexive'));

    var inspect = el('button', 'chip chip-action', 'see the table');
    inspect.onclick = function (event) {
      event.stopPropagation();   // don't also flip the card
      inspectCurrent();
    };
    chips.appendChild(inspect);

    $('card-answer').hidden = !revealed;
    $('drill-progress').textContent =
      (position + 1) + ' of ' + queue.length + ' · shuffled, nothing recorded';
    $('drill-hint').innerHTML = revealed
      ? '<kbd>space</kbd> next · <kbd>←</kbd> back · <kbd>s</kbd> say it again · <kbd>t</kbd> full table'
      : '<kbd>space</kbd> or tap to reveal · swipe to skip';
  }

  function advance(step) {
    if (!queue.length) return;
    position = (position + step + queue.length) % queue.length;
    revealed = false;
    renderCard();
  }

  function flipOrAdvance() {
    if (!queue.length) return;
    if (!revealed) {
      revealed = true;
      renderCard();
      speak(queue[position].form);
    } else {
      advance(1);
    }
  }

  /* Tap flips, horizontal swipe moves. Vertical drags are left to the page. */
  function bindGestures(node) {
    var startX = 0, startY = 0, swiped = false;

    node.addEventListener('touchstart', function (event) {
      if (event.touches.length !== 1) return;
      startX = event.touches[0].clientX;
      startY = event.touches[0].clientY;
      swiped = false;
    }, { passive: true });

    node.addEventListener('touchend', function (event) {
      var touch = event.changedTouches[0];
      var dx = touch.clientX - startX;
      var dy = touch.clientY - startY;
      if (Math.abs(dx) > 48 && Math.abs(dx) > Math.abs(dy)) {
        swiped = true;
        advance(dx < 0 ? 1 : -1);
      }
    }, { passive: true });

    // A swipe also fires a click on touch devices; ignore that one.
    node.addEventListener('click', function () {
      if (swiped) { swiped = false; return; }
      flipOrAdvance();
    });
  }

  /* Jump from a revealed card to that verb's table, opened on the tense that
   * just caught you out. */
  function inspectCurrent() {
    if (!queue.length) return;
    var card = queue[position];
    tableVerb = card.verb;
    tableTense = card.tense.id;
    $('table-search').value = card.verb.h;
    $('table-tense').value = card.tense.id;
    showScreen('tables');
  }

  /* ── tables screen ──────────────────────────────────── */

  var tableVerb = null;
  var tableTense = 'all';

  function renderTableTenses() {
    var select = $('table-tense');
    select.innerHTML = '';
    var all = el('option', null, 'All tenses');
    all.value = 'all';
    select.appendChild(all);
    deck.tenses.forEach(function (tense) {
      var option = el('option', null, tenseLabel(tense));
      option.value = tense.id;
      select.appendChild(option);
    });
    select.value = tableTense;
    select.onchange = function () { tableTense = select.value; renderTable(); };
  }

  /* No suggestions until something is typed: the old list ran to eighteen
   * chips before the table even started. */
  function renderTableResults(term) {
    var host = $('table-results');
    host.innerHTML = '';
    var needle = term.trim().toLowerCase();
    if (!needle) return;

    var matches = deck.verbs.filter(function (verb) {
      return verb.h.toLowerCase().indexOf(needle) === 0 ||
        (verb.t || '').toLowerCase().indexOf(needle) !== -1;
    }).slice(0, 8);

    if (!matches.length) {
      host.appendChild(el('p', 'hint', 'No verb matches that.'));
      return;
    }
    matches.forEach(function (verb) {
      var button = el('button', tableVerb === verb ? 'is-active' : null, verb.h);
      button.onclick = function () {
        tableVerb = verb;
        renderTableResults(term);
        renderTable();
      };
      host.appendChild(button);
    });
  }

  function renderTable() {
    var host = $('table-body');
    host.innerHTML = '';
    if (!tableVerb) {
      host.appendChild(el('p', 'empty', 'Type a verb above to see its paradigm.'));
      return;
    }

    var wrap = el('div', 'paradigm');
    wrap.appendChild(el('h3', null, tableVerb.h));
    var bits = [tableVerb.t || 'no translation'];
    if (tableVerb.g) bits.push('gerund ' + tableVerb.g);
    if (tableVerb.pp) bits.push('participle ' + tableVerb.pp);
    bits.push(tableVerb.n != null ? 'rank ' + tableVerb.n : 'unranked');
    wrap.appendChild(el('p', 'sub', bits.join(' · ')));

    deck.tenses.forEach(function (tense) {
      if (tableTense !== 'all' && tense.id !== tableTense) return;
      var paradigm = tableVerb.p[tense.id];
      if (!paradigm) return;
      var table = el('table', 'ptable');
      table.appendChild(el('caption', null, tenseLabel(tense)));
      tense.persons.forEach(function (person, index) {
        var form = paradigm.f[index];
        var code = paradigm.c.charAt(index);
        var tr = el('tr');
        tr.appendChild(el('th', null, personLabel(person)));
        var td = el('td');
        if (form) {
          var strong = el('b');
          paintForm(strong, form, lessonAt(paradigm, index), code);
          td.appendChild(strong);
        } else {
          td.appendChild(el('span', null, '—'));
        }
        tr.appendChild(td);
        table.appendChild(tr);
      });
      wrap.appendChild(table);
    });

    var legend = el('div', 'legend');
    CODE_ORDER.forEach(function (code) {
      var item = el('span');
      var swatch = el('span', 'swatch');
      swatch.style.background = 'var(--c' + code + ')';
      item.appendChild(swatch);
      item.appendChild(el('span', null, deck.code_labels[code]));
      legend.appendChild(item);
    });
    wrap.appendChild(legend);
    host.appendChild(wrap);
  }

  /* ── screens ────────────────────────────────────────── */

  function showScreen(name) {
    if (name === 'setup' && soloVerb) {
      soloVerb = null;
      queue = [];
      refreshSummary();
    }
    ['setup', 'drill', 'tables'].forEach(function (screen) {
      $('screen-' + screen).classList.toggle('is-active', screen === name);
    });
    Array.prototype.forEach.call(document.querySelectorAll('#tabs .tab'), function (tab) {
      tab.classList.toggle('is-active', tab.dataset.screen === name);
    });
    if (name === 'drill' && !queue.length) {
      queue = buildQueue(currentSelection());
      position = 0;
      revealed = false;
      renderCard();
    }
    if (name === 'tables') {
      renderTableResults($('table-search').value);
      renderTable();
    }
  }

  function startDrill() {
    queue = buildQueue(currentSelection());
    position = 0;
    revealed = false;
    renderCard();
    showScreen('drill');
    // Keep the space bar meaning "reveal", not "press the button I just used".
    if (document.activeElement && document.activeElement.blur) document.activeElement.blur();
  }

  /* ── boot ───────────────────────────────────────────── */

  function loadDeck(payload) {
    deck = payload;
    var speechName = SPEECH_LANGUAGE[deck.language];
    if (speechName) window.selectedLanguage = speechName;

    state.tenses = {};
    // Start on one tense only — the simple present of the indicative, which
    // every language in this shape has — rather than every mood's present.
    var opening = deck.tenses.filter(function (tense) {
      return !tense.compound && /^indic/i.test(tense.mood) && /^(pres|prés)/i.test(tense.tense);
    })[0] || deck.tenses.filter(function (tense) { return !tense.compound; })[0];
    deck.tenses.forEach(function (tense) { state.tenses[tense.id] = false; });
    if (opening) state.tenses[opening.id] = true;

    state.persons = {};
    deck.person_order.forEach(function (person) { state.persons[person] = true; });
    state.patterns = {};
    deck.patterns.forEach(function (pattern) { state.patterns[pattern.d] = true; });

    expandedMoods = {};
    renderDeckPicker();
    renderTenses();
    renderPersons();
    computeFamilies();
    renderDirection();
    renderClue();
    renderPatterns();
    renderCoverage();
    renderProvenance();
    renderTableTenses();
    refreshSummary();
    tableVerb = null;
    queue = [];
  }

  function setPatterns(predicate) {
    deck.patterns.forEach(function (pattern) {
      state.patterns[pattern.d] = predicate(pattern);
    });
    renderPatterns();
    refreshSummary();
  }

  function requestedLanguage() {
    var params = new URLSearchParams(window.location.search);
    var lang = (params.get('lang') || '').trim().toLowerCase();
    if (lang && decks[lang]) return lang;
    var codes = Object.keys(decks);
    return codes.length ? codes[0] : null;
  }

  function leaveConjugationMode(event) {
    if (event) event.preventDefault();
    try {
      if (document.referrer && window.history.length > 1) {
        var origin = new URL(document.referrer);
        if (origin.origin === window.location.origin && origin.pathname.indexOf('/conjugation') === -1) {
          history.back();
          return;
        }
      }
    } catch (error) { /* fall through to the study home */ }
    window.location.href = '../';
  }

  /* One entry point from the app: conjugation/?lang=pt&verb=ter drills that
   * verb across every tense it has. ?view=table opens the paradigm instead. */
  function applyDeepLink() {
    var params = new URLSearchParams(window.location.search);
    var wanted = (params.get('verb') || '').trim().toLowerCase();
    if (!wanted) return false;

    var verb = deck.verbs.filter(function (v) {
      return v.h.toLowerCase() === wanted;
    })[0];
    if (!verb) {
      $('table-search').value = wanted;
      showScreen('tables');
      renderTableResults(wanted);
      return true;
    }

    tableVerb = verb;
    $('table-search').value = verb.h;
    if (params.get('view') === 'table') {
      var tense = params.get('tense');
      tableTense = tense && tenseById(tense) ? tense : 'all';
      $('table-tense').value = tableTense;
      showScreen('tables');
      return true;
    }

    // Drill this verb alone: every tense it has, scope wide enough to
    // include it however rare it is.
    deck.tenses.forEach(function (t) {
      state.tenses[t.id] = !!verb.p[t.id];
      if (state.tenses[t.id]) expandedMoods[t.mood] = true;
    });
    state.scope = 100;
    $('scope').value = 100;
    CODE_ORDER.forEach(function (code) { state.types[code] = true; });
    soloVerb = verb;
    renderTenses();
    refreshSummary();
    startDrill();
    return true;
  }

  window.conjugationBoot = function () {
    var codes = Object.keys(decks);
    if (!codes.length) {
      document.querySelector('main').innerHTML =
        '<p class="empty">No deck loaded. Run ' +
        '<code>scripts/build_conjugation_drill.py</code> first.</p>';
      return;
    }

    loadDeck(decks[requestedLanguage()]);

    $('back-to-study').onclick = leaveConjugationMode;
    $('scope').oninput = function () {
      state.scope = parseInt(this.value, 10);
      refreshSummary();
    };
    $('start').onclick = startDrill;
    $('table-search').oninput = function () { renderTableResults(this.value); };

    $('patterns-all').onclick = function () { setPatterns(function () { return true; }); };
    $('patterns-none').onclick = function () { setPatterns(function () { return false; }); };
    $('patterns-irregular').onclick = function () {
      setPatterns(function (pattern) { return pattern.d !== ''; });
    };
    bindGestures($('card'));

    Array.prototype.forEach.call(document.querySelectorAll('[data-screen]'), function (node) {
      node.addEventListener('click', function () { showScreen(node.dataset.screen); });
    });

    document.addEventListener('keydown', function (event) {
      if (!$('screen-drill').classList.contains('is-active')) return;
      var isSpace = event.code === 'Space' || event.key === ' ' || event.key === 'Spacebar';
      if (isSpace) { event.preventDefault(); flipOrAdvance(); }
      if (event.key === 't' || event.key === 'T') inspectCurrent();
      if ((event.key === 's' || event.key === 'S') && revealed && queue.length) {
        speak(queue[position].form);
      }
      if (event.key === 'ArrowRight') advance(1);
      if (event.key === 'ArrowLeft') advance(-1);
    });

    if (!applyDeepLink()) showScreen('setup');
  };
})();
