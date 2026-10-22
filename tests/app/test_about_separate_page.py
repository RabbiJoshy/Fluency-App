from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / 'app'


class AboutSeparatePageTests(unittest.TestCase):
    """About is its own page (about.html), divorced from the app: it loads no
    sign-in, language, deck or progress, so it is the same for everyone."""

    def test_about_page_loads_none_of_the_app(self):
        page = (APP / 'about.html').read_text()
        about = (APP / 'js' / 'about-page.js').read_text()
        self.assertIn('js/about-page.js', page)
        for app_only in ['main.js', 'auth.js', 'passwordless', 'clerk', 'flashcards.js']:
            self.assertNotIn(app_only, page)
        imports = re.findall(r"^import .*?'\./([\w-]+\.js)", about, re.M)
        self.assertEqual(sorted(imports), ['card-replica.js', 'prominence-badge.js', 'walkthrough.js'])
        for app_only in ['currentUser', 'selectedLanguage', 'localStorage', 'config.languages']:
            self.assertNotIn(app_only, about)

    def test_app_has_no_about_inside_it(self):
        html = (APP / 'index.html').read_text()
        auth = (APP / 'js' / 'auth.js').read_text()
        self.assertNotIn('id="aboutProjectModal"', html)
        self.assertNotIn('id="walkthroughModal"', html)
        for gone in ['openAboutProjectModal', 'renderMarkdown', 'mountAboutDemos', '_signInAfterAbout']:
            self.assertNotIn(gone, auth)

    def test_every_in_app_entry_opens_the_page_in_a_new_tab(self):
        auth = (APP / 'js' / 'auth.js').read_text()
        self.assertIn("new URL('about.html', window.location.href).href, '_blank', 'noopener'", auth)
        for name in ['desktop-shell.js', 'main.js', 'ui.js']:
            self.assertNotIn('openAboutProjectModal', (APP / 'js' / name).read_text(), name)

    def test_old_links_are_forwarded_before_the_app_loads(self):
        html = (APP / 'index.html').read_text()
        forward = html.index("location.replace('about.html'")
        self.assertLess(forward, html.index('<script type="module"'))

    def test_service_worker_never_stores_about_as_the_app_shell(self):
        sw = (APP / 'service-worker.js').read_text()
        self.assertIn("isAppShell ? scopedPath('/index.html') : request", sw)

    def test_about_ignores_the_apps_text_size_zoom(self):
        # "Bigger" text zooms the page; the walkthrough's measured leader
        # lines then missed their elements and cards ran past the banners.
        page = (APP / 'about.html').read_text()
        self.assertIn("root.dataset.textSize = 'normal';", page)
        self.assertNotIn('fluency_text_size_v1', page)

    def test_demo_rows_outrank_the_live_card_row_grid(self):
        css = (APP / 'css' / 'style.css').read_text()
        self.assertIn('.about-demo-card-inner .meaning-row.meaning-row-regular {', css)


if __name__ == '__main__':
    unittest.main()
