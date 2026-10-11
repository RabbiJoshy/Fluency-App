import json
from pathlib import Path
import struct
import unittest


APP_ROOT = Path(__file__).resolve().parents[2] / "app"


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
        self.assertEqual(png_size(APP_ROOT / "icons/apple-touch-icon.png"), (180, 180))
        self.assertNotIn("Flashcards</title>", html)

    def test_icons_are_cached_for_offline_use(self) -> None:
        worker = (APP_ROOT / "service-worker.js").read_text(encoding="utf-8")
        for name in ("apple-touch-icon.png", "icon-192.png", "icon-512.png"):
            self.assertIn(f"'/icons/{name}'", worker)


if __name__ == "__main__":
    unittest.main()
