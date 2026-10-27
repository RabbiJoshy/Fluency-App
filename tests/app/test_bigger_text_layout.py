"""Tests for bigger-sized text accessibility, zoom compensations, and layout budgeting."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]


class BiggerTextLayoutTests(unittest.TestCase):
    def setUp(self):
        self.style_css = (ROOT / 'app/css/style.css').read_text('utf-8')
        self.progress_css = (ROOT / 'app/css/progress-overview.css').read_text('utf-8')
        self.auth_css = (ROOT / 'app/css/passwordless-auth.css').read_text('utf-8')
        self.refinements_css = (ROOT / 'app/css/ui-refinements.css').read_text('utf-8')
        self.flashcards_js = (ROOT / 'app/js/flashcards.js').read_text('utf-8')
        self.theme_js = (ROOT / 'app/js/theme.js').read_text('utf-8')
        self.spotify_js = (ROOT / 'app/js/spotify.js').read_text('utf-8')
        self.pills_js = (ROOT / 'app/js/card-metadata-pills.js').read_text('utf-8')

    def test_pin_mode_collapses_sentence_with_display_none(self):
        """Pin mode hides non-meaning elements using display:none so invisible blocks don't consume space."""
        pattern = re.compile(
            r'\.card-back:has\(\.pin-mode-hint:not\(\.is-notice\)\)\s+\.card-details\s*>\s*:not\([^)]+\)\s*\{\s*display:\s*none\s*!important;'
        )
        self.assertTrue(pattern.search(self.style_css), "Pin mode must set display:none !important on hidden card details")

    def test_available_height_ignores_hidden_and_none_children(self):
        """availableHeightForMeaningScroll must ignore elements that are display:none or visibility:hidden."""
        func_start = self.flashcards_js.find('function availableHeightForMeaningScroll(')
        self.assertGreater(func_start, -1)
        func_body = self.flashcards_js[func_start:func_start + 1200]
        self.assertIn("cs.display === 'none' || cs.visibility === 'hidden'", func_body)

    def test_refit_scroll_has_subpixel_tolerance(self):
        """refitMeaningScroll and updateCard must include subpixel tolerance buffer to avoid spurious scrollbars."""
        self.assertIn('scroll.scrollHeight > available + 2', self.flashcards_js)
        self.assertIn('scroll.scrollHeight > availableForScroll + 2', self.flashcards_js)

    def test_apply_text_size_announces_and_dispatches_resize(self):
        """applyTextSize must announce fluency-text-size-change and dispatch resize so active card re-measures."""
        self.assertIn('fluency-text-size-change', self.theme_js)
        self.assertIn("dispatchEvent(new Event('resize'))", self.theme_js)

    def test_tooltips_and_popovers_account_for_layout_zoom(self):
        """Body-anchored popovers must scale getBoundingClientRect coordinates by layout zoom."""
        self.assertIn('function currentLayoutZoom()', self.flashcards_js)
        self.assertIn('at.top / zoom', self.flashcards_js)
        self.assertIn('rect.top / zoom', self.flashcards_js)
        self.assertIn('rect.top / zoom', self.spotify_js)
        self.assertIn('anchor.bottom / zoom', self.pills_js)

    def test_front_pos_pill_width_check_scales_by_zoom(self):
        """Front POS pill fit comparison must divide getBoundingClientRect width by zoom factor."""
        pill_check = 'group.getBoundingClientRect().width / frontZoom > room - 4'
        self.assertIn(pill_check, self.flashcards_js)

    def test_modals_compensate_dvh_units_for_ui_zoom(self):
        """Modals using dvh units must divide by --ui-zoom to prevent overflowing the viewport."""
        self.assertIn('max-height: calc(100dvh / var(--ui-zoom, 1) - 32px);', self.style_css)
        self.assertIn('max-height: min(620px, calc(100dvh / var(--ui-zoom, 1) - 40px));', self.style_css)
        self.assertIn('max-height: min(calc(70dvh / var(--ui-zoom, 1)), 560px);', self.style_css)
        self.assertIn('max-height: calc(100dvh / var(--ui-zoom, 1) - 86px);', self.style_css)
        self.assertIn('max-height: min(calc(90dvh / var(--ui-zoom, 1)), 920px);', self.progress_css)
        self.assertIn('max-height: calc(100dvh / var(--ui-zoom, 1) - 24px);', self.progress_css)
        self.assertIn('height: calc(100dvh / var(--ui-zoom, 1));', self.auth_css)
        self.assertIn('max-height: calc(85dvh / var(--ui-zoom, 1));', self.refinements_css)

    def test_action_tray_labels_have_ellipsis_protection(self):
        """Action tray ref-tile labels must have ellipsis overflow protection on mobile."""
        self.assertIn('text-overflow: ellipsis;', self.style_css)
        pattern = re.compile(r'\.links-section:has\(>\s*:nth-child\(5\)\)\s*\.ref-tile-label\s*\{[^}]*font-size:\s*13px;')
        self.assertTrue(pattern.search(self.style_css), "Mobile 5-tile tray must step font-size down to 13px")


if __name__ == '__main__':
    unittest.main()
