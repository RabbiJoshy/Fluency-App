import importlib.util
import json
from pathlib import Path
import struct
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = REPOSITORY_ROOT / "app"
_spec = importlib.util.spec_from_file_location("build_pages_site", REPOSITORY_ROOT / "scripts/build_pages_site.py")
build_pages_site = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(build_pages_site)


def png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()[:24]
    assert data[:8] == b"\x89PNG\r\n\x1a\n", path
    return struct.unpack(">II", data[16:24])


class HomeScreenIdentityTests(unittest.TestCase):
    """Adding the app to a home screen must show Fluency and the F mark.

    iOS ignores SVG apple-touch-icons, so the icons have to be real PNGs.
    """

    def test_manifest_names_the_app_and_points_at_png_icons(self) -> None:
        manifest = json.loads((APP_ROOT / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["name"], "Fluency")
        self.assertEqual(manifest["short_name"], "Fluency")
        sizes = {}
        for icon in manifest["icons"]:
            self.assertEqual(icon["type"], "image/png")
            width, height = png_size(APP_ROOT / icon["src"])
            self.assertEqual(icon["sizes"], f"{width}x{height}")
            sizes[width] = icon["src"]
        self.assertIn(192, sizes)
        self.assertIn(512, sizes)

    def test_ios_tags_use_the_same_name_and_a_png_touch_icon(self) -> None:
        html = (APP_ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('<meta name="apple-mobile-web-app-title" content="Fluency">', html)
        self.assertIn('<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">', html)
        # 512 rather than 180: iOS scales it down, and it stays sharp on larger icon grids.
        self.assertEqual(png_size(APP_ROOT / "icons/apple-touch-icon.png"), (512, 512))
        self.assertNotIn("Flashcards</title>", html)

    def test_manifest_link_is_versioned_so_an_old_worker_cannot_serve_it_stale(self) -> None:
        html = (APP_ROOT / "index.html").read_text(encoding="utf-8")
        self.assertRegex(html, r'<link rel="manifest" href="manifest\.json\?v=[^"]+">')
        self.assertIn('href="manifest.json?v=stg-abc"', build_pages_site.stamp(html, "stg-abc"))

    def test_icons_are_cached_for_offline_use(self) -> None:
        worker = (APP_ROOT / "service-worker.js").read_text(encoding="utf-8")
        for name in ("apple-touch-icon.png", "icon-192.png", "icon-512.png"):
            self.assertIn(f"'/icons/{name}'", worker)

    def test_staging_build_renames_to_beta_and_swaps_every_icon(self) -> None:
        for rel in build_pages_site.STAGING_IDENTITY_FILES:
            original = (APP_ROOT / rel).read_bytes()
            staged = build_pages_site.staging_identity(rel, original).decode("utf-8")
            if rel != "service-worker.js":
                self.assertIn("Fluency β", staged, rel)
            for name in ("apple-touch-icon.png", "icon-192.png", "icon-512.png"):
                if f"icons/{name}" in original.decode("utf-8"):
                    self.assertIn(f"icons/staging/{name}", staged, rel)
                    self.assertNotIn(f"'/icons/{name}'", staged, rel)
        manifest = json.loads(build_pages_site.staging_identity("manifest.json", (APP_ROOT / "manifest.json").read_bytes()))
        self.assertEqual(manifest["name"], "Fluency β")
        self.assertEqual(manifest["short_name"], "Fluency β")
        staged_html = build_pages_site.staging_identity("index.html", (APP_ROOT / "index.html").read_bytes()).decode("utf-8")
        self.assertIn('content="Fluency β">', staged_html)
        self.assertIn("<title>Fluency β</title>", staged_html)
        for icon in manifest["icons"]:
            self.assertEqual(png_size(APP_ROOT / icon["src"]), tuple(map(int, icon["sizes"].split("x"))))
        self.assertEqual(png_size(APP_ROOT / "icons/staging/apple-touch-icon.png"), (512, 512))


if __name__ == "__main__":
    unittest.main()
