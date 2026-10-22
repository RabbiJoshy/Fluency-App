from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]


class AboutSeparatePageTests(unittest.TestCase):
    """About is its own page in its own tab, the same for everyone: it never
    reads or starts a sign-in and has no account-dependent buttons."""

    def test_about_route_skips_sign_in_before_reading_the_saved_user(self):
        auth = (ROOT / 'app/js/auth.js').read_text()
        about = auth.index("if (parseRoute(window.location.hash).kind === 'about') return;")
        saved = auth.index("const savedUser = localStorage.getItem('flashcardUser');")
        self.assertLess(about, saved)
        self.assertNotIn('_signInAfterAbout', auth)

    def test_no_account_dependent_controls(self):
        auth = (ROOT / 'app/js/auth.js').read_text()
        html = (ROOT / 'app/index.html').read_text()
        for gone in ['_appendAboutCTAs', 'Back to the app', '_aboutReturnTo']:
            self.assertNotIn(gone, auth)
        self.assertNotIn('closeAboutProjectModal', html)

    def test_every_in_app_entry_opens_a_new_tab(self):
        sources = {name: (ROOT / 'app/js' / name).read_text()
                   for name in ['auth.js', 'desktop-shell.js', 'main.js', 'ui.js']}
        self.assertIn("'_blank', 'noopener'", sources['auth.js'])
        for name, text in sources.items():
            calls = re.findall(r'(?<!function )openAboutProjectModal\?*\.?\(', text)
            # Only the boot path for #/about (main.js) opens the page in place.
            allowed = 1 if name == 'main.js' else 0
            self.assertLessEqual(len(calls), allowed, name)

    def test_resume_prompt_stays_off_the_about_page(self):
        vocab = (ROOT / 'app/js/vocab.js').read_text()
        self.assertIn("['tutorial', 'about'].includes(window.fluencyRoute?.kind)", vocab)


if __name__ == '__main__':
    unittest.main()
