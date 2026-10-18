"""Companion navigation and partially learned cycle rows keep their boundaries."""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(shutil.which('node'), 'Node.js required')
class UiRefinementTests(unittest.TestCase):
    def test_companion_navigation_and_cycle_knowledge(self):
        script = r"""
        const fs = require('node:fs'), vm = require('node:vm'), assert = require('node:assert/strict');
        const cards = fs.readFileSync('app/js/flashcards.js', 'utf8');
        const knowledge = fs.readFileSync('app/js/knowledge.js', 'utf8');
        const c = {
            window: {}, currentIndex: 0, cardNavStack: [],
            flashcards: [
                { targetWord: 'fue', splitInfo: { index: 1 } },
                { targetWord: 'fue', splitInfo: { index: 2 } },
                { targetWord: 'otro', splitInfo: { index: 2 } }
            ],
            goToDeckCard(index) { c.currentIndex = index; },
            stepToSplitSibling(direction) { c.direction = direction; return true; },
            stats: { levelNumber: 4 },
            getKnowledgeFocusItems: () => [
                { meaningIndex: 0, learned: true },
                { meaningIndex: 0, learned: false },
                { meaningIndex: 1, learned: true },
                { meaningIndex: 2, learned: false, needsReview: true, reviewReason: 'incorrect' }
            ],
            getKnowledgeItemState: (_card, item) => item
        };
        vm.createContext(c);
        vm.runInContext(cards.slice(cards.indexOf('function selectSplitCompanion('),
            cards.indexOf('function stepToSplitSibling(')), c);
        let stopped = 0;
        const event = { preventDefault() {}, stopPropagation() { stopped++; } };
        c.selectSplitCompanion(event, 2);
        assert.equal(c.currentIndex, 1);
        c.selectSplitCompanion(event, 1);
        assert.equal(c.currentIndex, 0);
        c.selectSplitCompanion(event, 1);
        assert.equal(c.currentIndex, 0);
        c.flashcards[1].targetWord = 'different';
        c.selectSplitCompanion(event, 2);
        assert.equal(c.currentIndex, 0, 'never navigate to an unrelated word');
        c.cardNavStack = [{}];
        c.flashcards[0]._splitNext = { targetWord: 'fue', splitInfo: { index: 2 } };
        c.showSplitSibling = card => { c.selected = card.splitInfo.index; };
        c.selectSplitCompanion(event, 2);
        assert.equal(c.selected, 2, 'linked word views select the requested sibling');
        assert.equal(stopped, 5);
        assert.equal(c.currentStudyLevelLabel(), 'Level 4');
        c.stats.levelNumber = null;
        assert.equal(c.currentStudyLevelLabel(), '');
        vm.runInContext(knowledge.slice(knowledge.indexOf('function getPracticeMeaningInfo('),
            knowledge.indexOf('function getPracticeMeaningIndices(')), c);
        const info = c.getPracticeMeaningInfo({});
        assert.deepEqual([...info.known], [1], 'a partly learned cycle must remain active');
        assert.deepEqual([...info.indices], [2]);
        assert.equal(info.practising, 1);
        """
        result = subprocess.run(['node', '-'], input=script, text=True,
                                capture_output=True, cwd=ROOT)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_exact_three_companion_selection(self):
        script = r"""
        const fs = require('node:fs'), vm = require('node:vm'), assert = require('node:assert/strict');
        const source = fs.readFileSync('app/js/flashcards.js', 'utf8');
        const c = { window: {}, stats: {}, cardNavStack: [{}], currentIndex: 0,
            currentMeaningIndex: 2, currentExampleIndex: 2, currentMWEIndex: 2,
            currentGroupSelection: {}, document: { getElementById: () => null },
            updateCard() {}, goToDeckCard(index) { c.currentIndex = index; } };
        vm.createContext(c);
        vm.runInContext(source.slice(source.indexOf('function selectSplitCompanion('),
            source.indexOf('// Plain forward step')), c);
        const event = { preventDefault() {}, stopPropagation() {} };
        for (const order of [[1,2,3],[2,3,1],[3,1,2]]) {
            const cards = order.map(index => ({ targetWord:'fue', splitInfo:{index} }));
            cards.forEach((card, index) => {
                card._splitNext = cards[index+1]; card._splitPrev = cards[index-1];
            });
            for (const from of cards) for (const to of cards) {
                c.flashcards = [from]; c.selectSplitCompanion(event, to.splitInfo.index);
                assert.equal(c.flashcards[0], to);
                assert.equal(c.cardNavStack.length, 1);
            }
            c.flashcards = [cards[0]];
            assert(c.stepToSplitSibling()); assert(c.stepToSplitSibling());
            assert.equal(c.stepToSplitSibling(), false);
        }
        c.cardNavStack = [];
        c.flashcards = [1,2,3].map(index => ({targetWord:'fue',splitInfo:{index}}));
        for (let from=0; from<3; from++) for (let to=0; to<3; to++) {
            c.currentIndex=from; c.selectSplitCompanion(event,to+1); assert.equal(c.currentIndex,to);
        }
        """
        result = subprocess.run(['node', '-'], input=script, text=True, capture_output=True, cwd=ROOT)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_settings_modal_hierarchy_and_preferred_ai_dropdown(self):
        index_html = (ROOT / 'app' / 'index.html').read_text(encoding='utf-8')
        style_css = (ROOT / 'app' / 'css' / 'style.css').read_text(encoding='utf-8')
        ui_css = (ROOT / 'app' / 'css' / 'ui-refinements.css').read_text(encoding='utf-8')
        ai_pref_js = (ROOT / 'app' / 'js' / 'ai-preference.js').read_text(encoding='utf-8')

        # 1. Languages you know is at the top of Study settings pane (before settings-preference-group)
        study_pane_start = index_html.find('id="settingsPaneStudy"')
        self.assertNotEqual(study_pane_start, -1)
        study_pane = index_html[study_pane_start:index_html.find('</section>', study_pane_start)]
        known_langs_idx = study_pane.find('id="settingsKnownLanguagesBtn"')
        pref_group_idx = study_pane.find('class="settings-preference-group"')
        self.assertNotEqual(known_langs_idx, -1)
        self.assertNotEqual(pref_group_idx, -1)
        self.assertLess(known_langs_idx, pref_group_idx, "Languages you know must be above settings-preference-group")

        # 2. About this app is removed from App pane
        app_pane_start = index_html.find('id="settingsPaneApp"')
        self.assertNotEqual(app_pane_start, -1)
        app_pane = index_html[app_pane_start:index_html.find('</section>', app_pane_start)]
        self.assertNotIn('settingsAboutBtn', app_pane)

        # 3. Your Words buttons do not have is-primary (purple)
        words_pane_start = index_html.find('id="settingsPaneWords"')
        self.assertNotEqual(words_pane_start, -1)
        words_pane = index_html[words_pane_start:index_html.find('</section>', words_pane_start)]
        self.assertNotIn('settings-words-row is-primary', words_pane)

        # 4. Account tab: User profile is at the top, Preferred AI is at the bottom
        account_tab_start = index_html.find('id="accountTabContent"')
        self.assertNotEqual(account_tab_start, -1)
        account_tab = index_html[account_tab_start:index_html.find('id="aboutTabContent"')]
        profile_idx = account_tab.find('class="account-profile" aria-label="Your profile"')
        spotify_idx = account_tab.find('class="account-profile account-spotify"')
        ai_idx = account_tab.find('class="account-profile account-ai"')
        self.assertNotEqual(profile_idx, -1)
        self.assertNotEqual(spotify_idx, -1)
        self.assertNotEqual(ai_idx, -1)
        self.assertLess(profile_idx, spotify_idx, "User profile must come before Spotify")
        self.assertLess(spotify_idx, ai_idx, "Preferred AI must be at the bottom of Account tab")

        # 5. Preferred AI has no sign in link and has punchy description
        self.assertNotIn('preferredAiLogin', account_tab)
        self.assertIn('Used when copying and pasting to AI', account_tab)

        # 6. Preferred AI has circular avatar, trigger, and menu with both logos
        self.assertIn('id="preferredAiAvatar"', account_tab)
        self.assertIn('id="preferredAiDropdown"', account_tab)
        self.assertIn('id="preferredAiTrigger"', account_tab)
        self.assertIn('id="preferredAiMenu"', account_tab)
        self.assertIn('data-value="chatgpt"', account_tab)
        self.assertIn('data-value="claude"', account_tab)

        # 7. Words action buttons do not turn purple on hover
        self.assertNotIn('button.settings-words-row:hover .settings-words-action {\n  border-color: var(--accent-primary);', style_css)

        # 8. AI preferences script paints circular avatar and dropdown
        self.assertIn('account-avatar--ai', ai_pref_js)
        self.assertIn('preferredAiTrigger', ai_pref_js)
        self.assertIn('preferredAiMenu', ai_pref_js)

    def test_level_progress_legend_omits_zero_counts(self):
        ui_js = (ROOT / 'app/js/ui.js').read_text(encoding='utf-8')
        # Stats are only included if > 0 (New always shows, even at 0)
        self.assertIn("segments.filter(([kind, , n]) => n > 0 || kind === 'new')", ui_js)
        self.assertIn("['seen', 'Seen', levelReviewCount]", ui_js)
        self.assertIn("['known', 'Known', levelKnownCount]", ui_js)

    def test_smart_skip_unified_toggle_button(self):
        index_html = (ROOT / 'app/index.html').read_text(encoding='utf-8')
        fast_mode_js = (ROOT / 'app/js/fast-mode.js').read_text(encoding='utf-8')
        css = (ROOT / 'app/css/ui-refinements.css').read_text(encoding='utf-8')

        # Button exists with role switch and state label
        self.assertIn('id="smartSkipToggleBtn"', index_html)
        self.assertIn('class="home-switch" role="switch"', index_html)
        self.assertIn('id="smartSkipStateLabel"', index_html)

        # JS wires click handler and updates label on refresh
        self.assertIn("document.getElementById('smartSkipToggleBtn')?.addEventListener('click'", fast_mode_js)
        self.assertIn("toggleBtn.classList.toggle('is-on', on)", fast_mode_js)
        self.assertIn("stateLabel.textContent = on ? 'On' : 'Off'", fast_mode_js)

        # The home strip is one line: a compact switch, not a second 52px pill
        # competing with the Learn button.
        home_css = (ROOT / 'app/css/home-layout.css').read_text(encoding='utf-8')
        self.assertIn('.home-switch[aria-checked="true"]', home_css)
        self.assertIn('.home-smart-skip.is-on', home_css)
        self.assertNotIn('class="smart-skip-toggle-btn"', index_html)

    def test_setup_headings_and_level_spacing(self):
        style_css = (ROOT / 'app/css/style.css').read_text(encoding='utf-8')
        # Setup container/panel top padding trimmed so content starts higher
        self.assertIn('.container:has(#setupPanel:not(.hidden)) { padding-top: 10px; }', style_css)
        self.assertIn('#setupPanel.file-upload { padding-top: 2px; }', style_css)
        # Choose a level header has tighter top padding and breathing room below
        self.assertIn('#step2 > .step-header { margin: 0; padding: 2px 4px 14px; }', style_css)
        self.assertIn('#step2 .level-choosing { margin-top: 2px; }', style_css)
        # Choose your vocabulary header starts higher and has breathing gap to bullets
        self.assertIn('#step1.language-summary-active #standardSourceCard { padding-top: 6px; padding-bottom: 18px; }', style_css)
        self.assertIn('.standard-source-choice-intro { display: grid; gap: 14px; }', style_css)

    def test_practice_text_centered(self):
        style_css = (ROOT / 'app/css/style.css').read_text(encoding='utf-8')
        refinements_css = (ROOT / 'app/css/ui-refinements.css').read_text(encoding='utf-8')
        self.assertIn('.review-deck-content { display: flex; flex-direction: column; align-items: center; text-align: center; gap: 12px; }', style_css)
        self.assertIn('#reviewDeckBody .review-deck-summary', refinements_css)
        self.assertIn('justify-content: center;', refinements_css)
        self.assertIn('text-align: center;', refinements_css)

    def test_smart_skip_blur_backdrop_animation(self):
        style_css = (ROOT / 'app/css/style.css').read_text(encoding='utf-8')
        fast_mode_js = (ROOT / 'app/js/fast-mode.js').read_text(encoding='utf-8')
        # Full screen backdrop blur CSS
        self.assertIn('.smart-skip-backdrop', style_css)
        self.assertIn('backdrop-filter: blur(10px);', style_css)
        self.assertIn('.smart-skip-backdrop.visible', style_css)
        # Centered toast CSS
        self.assertIn('.smart-skip-animation-toast {', style_css)
        self.assertIn('top: 50%;', style_css)
        self.assertIn('transform: translate(-50%, -50%) scale(1);', style_css)
        # JS attaches backdrop and handles lifecycle
        self.assertIn("backdrop.id = 'smartSkipBackdrop'", fast_mode_js)
        self.assertIn("backdrop.className = 'smart-skip-backdrop'", fast_mode_js)
        self.assertIn("backdrop.classList.add('visible')", fast_mode_js)
        self.assertIn("backdrop.classList.add('fade-out')", fast_mode_js)

