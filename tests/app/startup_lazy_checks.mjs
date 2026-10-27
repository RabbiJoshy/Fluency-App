import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import vm from 'node:vm';

const main = await readFile(new URL('../../app/js/main.js', import.meta.url), 'utf8');
const html = await readFile(new URL('../../app/index.html', import.meta.url), 'utf8');
assert.ok(!/^import .*['"].\/tutorial\.js/m.test(main), 'tutorial must leave the static boot graph');
assert.ok(!/<link[^>]+modulepreload[^>]+(?:tutorial|card-replica)\.js/.test(html));
const loader = main.slice(main.indexOf('let tutorialModulePromise = null;'), main.indexOf('function startCardTutorial('))
    .replace("import('./tutorial.js?v=20260929sense6')", 'loadTutorialModule()');
const introduction = main.slice(main.indexOf('async function openTutorialIntroduction()'), main.indexOf('function renderTutorialLanguageChoices()'));

function harness({ seen = false, language = 'spanish', mode = 'speech', modal = false, route = 'language', fail = false } = {}) {
    const counts = { loads: 0, opens: 0, firstRun: 0, alerts: 0, choices: 0 };
    const context = {
        localStorage: { getItem: () => seen ? '1' : null },
        console: { warn() {} },
        document: {
            getElementById(id) {
                if (id === 'step1') return { classList: { contains: name => name === 'source-speech-active' && mode === 'speech' } };
                if (id === 'tutorialIntroModal') return { classList: { remove() {} } };
                return null;
            },
            querySelector(selector) {
                if (selector === '.lang-tab.active') return language ? { dataset: { lang: language } } : null;
                return modal ? {} : null;
            },
        },
        renderTutorialLanguageChoices() { counts.choices++; },
        startCardTutorial() { counts.opens++; },
    };
    context.window = {
        fluencyRoute: { kind: route },
        alert() { counts.alerts++; },
    };
    context.loadTutorialModule = async () => {
        counts.loads++;
        if (fail) throw new Error('offline');
        context.window.openCardTutorial = () => { counts.opens++; };
        context.window.openFirstRunCardTutorial = () => { counts.firstRun++; };
        context.window.getCardTutorialLanguageKey = () => language;
    };
    vm.runInNewContext(loader + introduction, context);
    return { context, counts, setFail(value) { fail = value; } };
}

for (const options of [{ seen: true }, { route: 'word' }, { language: null }, { mode: null }, { modal: true }]) {
    const { context, counts } = harness(options);
    assert.equal(context.window.openFirstRunCardTutorial(), false);
    assert.equal(counts.loads, 0, 'ineligible onboarding must not fetch optional modules');
}
{
    const { context, counts } = harness();
    assert.equal(context.window.getCardTutorialMode(), 'speech');
    context.window.activeArtist = { language: 'spanish' };
    assert.equal(context.window.getCardTutorialMode(), 'lyrics');
    await Promise.all([context.window.openCardTutorial(), context.window.openCardTutorial()]);
    assert.equal(counts.loads, 1, 'concurrent taps must share the module request');
    assert.equal(counts.opens, 2);
}
{
    const { context, counts, setFail } = harness({ fail: true });
    await context.window.openCardTutorial();
    assert.equal(counts.alerts, 1);
    setFail(false);
    await context.window.openCardTutorial();
    assert.equal(counts.loads, 2, 'a failed request must remain retryable');
    assert.equal(counts.opens, 1);
}
{
    const { context, counts } = harness();
    assert.equal(context.window.openFirstRunCardTutorial(), true);
    await context.loadCardTutorial();
    await Promise.resolve();
    assert.equal(counts.firstRun, 1);
}
{
    const { context, counts } = harness({ language: null });
    await context.openTutorialIntroduction();
    assert.equal(counts.loads, 1);
    assert.equal(counts.choices, 1, 'language choices need the loaded tutorial adapters');
}
console.log('Lazy startup tutorial checks passed');
