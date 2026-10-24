"""Stdlib-only regression checks; no Sass compiler or theme activation needed."""

import hashlib
from pathlib import Path
import re
import unittest

import prepare_sources as prep


class PrepareSourcesTests(unittest.TestCase):
    def test_accent_tokens_are_fixed_before_widget_derivation(self):
        self.assertEqual(
            prep.transform("color: -st-accent-fg-color; background: st-lighten(-st-accent-color, 5%);"),
            "color: $gp-accent-fg; background: st-lighten($gp-accent-bg, 5%);",
        )

    def test_literal_colors_use_roles(self):
        self.assertEqual(
            prep.transform("color: white; background: #000; box-shadow: 0 0 2px rgba(0, 0, 0, .4);"),
            "color: $gp-shell-fg; background: $gp-shell-bg; box-shadow: 0 0 2px rgba($gp-shell-bg, .4);",
        )
        self.assertEqual(prep.transform("rgba(34, 34, 38, 0.98)"), "rgba($gp-shell-bg, 0.98)")
        with self.assertRaisesRegex(ValueError, "Unmapped literal color"):
            prep.transform("rgba(1, 2, 3, .5)")

    def test_occlusion_sentinel_is_preserved(self):
        self.assertEqual(prep.transform("rgba(3,2,1,0)"), "rgba(3,2,1,0)")

    def test_comments_strings_and_selectors_are_not_recolored(self):
        source = '// white -st-accent-color\n/* black */\ncontent: "white"; .white, #black { color: white; }'
        expected = source.replace("color: white;", "color: $gp-shell-fg;")
        self.assertEqual(prep.transform(source), expected)

    def test_resource_urls_use_existing_yaru_assets(self):
        for name in prep.THEME_ASSETS:
            self.assertEqual(
                prep.transform(f'url("{prep.RESOURCE_PREFIX}{name}")'),
                f'url("src/{name}")',
            )
        for name in prep.METRO_ASSETS:
            self.assertEqual(prep.transform(f'url("{name}")'), "none")
        for name in ("resource:///org/gnome/shell/theme/missing.svg", "./missing.svg"):
            with self.assertRaises(ValueError):
                prep.transform(f'url("{name}")')

    def test_complete_snapshot_has_no_dynamic_accents_or_broken_urls(self):
        sources = prep.prepared_sources()
        self.assertIn(Path("upstream/widgets/_quick-settings.scss"), sources)
        self.assertIn(Path("yaru/_dock.scss"), sources)
        self.assertIn(Path("yaru/_tweaks.scss"), sources)
        for path, source in sources.items():
            with self.subTest(path=path):
                code = re.sub(r"/\*.*?\*/|//[^\n]*", "", source, flags=re.DOTALL)
                self.assertNotIn("-st-accent-color", code)
                self.assertNotIn("-st-accent-fg-color", code)
                for url in re.findall(r'url\("([^\"]+)"\)', code):
                    self.assertTrue((prep.SHELL_DIR / url).is_file(), url)

    def test_preparation_is_deterministic_and_preserves_vendored_sources(self):
        originals = [*prep.UPSTREAM.rglob("*.scss"), *prep.YARU.rglob("*.scss")]
        before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in originals}
        count = prep.prepare()
        self.assertEqual(prep.prepare(check=True), count)
        first = {path: (prep.OUTPUT / path).read_bytes() for path in prep.prepared_sources()}
        prep.prepare()
        self.assertEqual(first, {path: (prep.OUTPUT / path).read_bytes() for path in first})
        self.assertEqual(before, {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in originals})


if __name__ == "__main__":
    unittest.main()
