import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("palette", ROOT / "scripts/palette.py")
assert SPEC is not None and SPEC.loader is not None
palette = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(palette)


class PaletteTests(unittest.TestCase):
    def test_current_palette_is_generated(self):
        palette.generate(check=True)

    def test_preserves_names_and_normalizes_hex(self):
        source = '{"petrol_blue": "#0080a9", "cascade": "#89a59e"}'
        rendered = palette.render_palette(source)
        self.assertIn("$petrol_blue: #0080A9;", rendered)
        self.assertIn("$cascade: #89A59E;", rendered)
        self.assertEqual(rendered, palette.render_palette(source))

    def test_rejects_duplicate_keys(self):
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            palette.render_palette('{"white":"#FFFFFF", "white":"#000000"}')

    def test_rejects_invalid_names(self):
        for name in ("$red", "red-color", "1red", "red; color"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                palette.render_palette('{"' + name + '": "#FFFFFF"}')

    def test_rejects_invalid_colors(self):
        for value in ('"red"', '"#fff"', '"#ZZ0000"', '"#123456;"', 'null', '123'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                palette.render_palette('{"red": ' + value + '}')

    def test_rejects_empty_or_nonobject_palette(self):
        for value in ("{}", "[]", '"red"', "null"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                palette.render_palette(value)


if __name__ == "__main__":
    unittest.main()
