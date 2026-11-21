"""Variant validation and isolated source staging; no compiler or desktop needed."""

import configparser
import importlib.util
import json
import re
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load_script(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    with patch.object(sys, "path", [str(ROOT / "scripts"), *sys.path]):
        spec.loader.exec_module(module)
    return module


variants = load_script("variant_test_helpers", "theme_variants.py")
builder = load_script("variant_test_builder", "build-theme.py")

# Public configuration keys and their generated semantic assignments.
OPTIONAL_MAPPINGS = {
    "shell_accent": ("gp-shell-accent-override",),
    "shell_toggle_bg": ("gp-shell-toggle-bg",),
    "shell_toggle_fg": ("gp-shell-toggle-fg",),
    "shell_toggle_focus_fg": ("gp-shell-toggle-focus-fg",),
    "sidebar_selection": ("gp-sidebar-selection-bg",),
    "gtk_accent": ("gp-accent-bg", "gp-control-accent-bg"),
}
PALETTE_ROLES = ("sidebar_base", "sidebar_hover", "sidebar_tint", *OPTIONAL_MAPPINGS)


def expected_assignments(definition):
    base = f"${definition['sidebar_base']}"
    if "sidebar_tint" in definition:
        base = f"mix({base}, ${definition['sidebar_tint']}, 80%)"
    result = {"gp-sidebar-base": base,
              "gp-sidebar-hover-color": f"${definition['sidebar_hover']}"}
    for option, roles in OPTIONAL_MAPPINGS.items():
        if option in definition:
            result.update({role: f"${definition[option]}" for role in roles})
    if "swap_content_surfaces" in definition:
        result["gp-swap-content-surfaces"] = str(definition["swap_content_surfaces"]).lower()
    return result


def scss_assignments(root):
    text = (root / "scss/_variant.scss").read_text(encoding="utf-8")
    lines = [line for line in text.splitlines() if line and not line.startswith("//")]
    matches = [re.fullmatch(r"\$([a-z-]+): (.+);", line) for line in lines]
    if not all(matches):
        raise AssertionError(f"Unexpected generated SCSS: {text}")
    result = {match[1]: match[2] for match in matches}
    if len(result) != len(lines):
        raise AssertionError("Duplicate generated SCSS assignments")
    return result


class VariantTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="variant-tests-")
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.root = self.directory / "arbitrary-checkout"
        self.root.mkdir()
        # Copy the curated inputs, not build caches or the entire checkout.
        for source in variants.project_files(ROOT):
            target = self.root / source.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        self.definitions = variants.load_variants(self.root)
        # Keep fixtures deterministic even when run from a Brown release archive.
        (self.root / "theme-variant").write_text("nile-blue\n", encoding="utf-8")
        variants.generate_variant(self.root)

    def write_variants(self, definitions):
        (self.root / "theme-variants.json").write_text(
            json.dumps(definitions), encoding="utf-8")

    def test_current_variants_and_active_selection(self):
        self.assertEqual(set(self.definitions), {"nile-blue", "brown"})
        self.assertEqual(variants.selected_variant(self.root),
                         ("nile-blue", self.definitions["nile-blue"]))
        palette = json.loads((self.root / "color-palette.json").read_text())
        for key, definition in self.definitions.items():
            with self.subTest(variant=key):
                self.assertEqual(definition["name"], {
                    "nile-blue": "Viparu-Nile-Blue", "brown": "Viparu-Brown"}[key])
                for role in PALETTE_ROLES:
                    if role in definition:
                        self.assertIn(definition[role], palette)
                self.assertIsInstance(definition.get("swap_content_surfaces", False), bool)

    def test_generated_scss_and_metadata_for_each_variant(self):
        original_selector = (self.root / "theme-variant").read_bytes()
        original_metadata = (self.root / "index.theme").read_bytes()
        original_scss = (self.root / "scss/_variant.scss").read_bytes()
        for key, definition in self.definitions.items():
            with self.subTest(variant=key):
                target = self.directory / key
                variants.copy_project(target, key, self.root)
                self.assertEqual(variants.generate_variant(target), key)
                self.assertEqual(variants.selected_variant(target), (key, definition))
                scss = (target / "scss/_variant.scss").read_text()
                self.assertEqual(scss_assignments(target), expected_assignments(definition))
                metadata = configparser.ConfigParser()
                metadata.read(target / "index.theme")
                self.assertEqual(metadata["Desktop Entry"]["Name"], definition["name"])
                self.assertEqual(metadata["X-GNOME-Metatheme"]["GtkTheme"], definition["name"])
                first = (target / "index.theme").read_bytes(), scss
                variants.generate_variant(target)
                self.assertEqual(first, ((target / "index.theme").read_bytes(),
                                         (target / "scss/_variant.scss").read_text()))
        self.assertEqual((self.root / "theme-variant").read_bytes(), original_selector)
        self.assertEqual((self.root / "index.theme").read_bytes(), original_metadata)
        self.assertEqual((self.root / "scss/_variant.scss").read_bytes(), original_scss)

    def test_rejects_empty_or_nonobject_definitions(self):
        for value in ({}, [], "brown", None):
            with self.subTest(value=value):
                self.write_variants(value)
                with self.assertRaisesRegex(ValueError, "nonempty object"):
                    variants.load_variants(self.root)

    def test_rejects_invalid_variant_ids(self):
        for key in ("Brown", "1brown", "brown_color", "../brown", ""):
            with self.subTest(key=key):
                self.write_variants({key: self.definitions["brown"]})
                with self.assertRaisesRegex(ValueError, "Invalid variant ID"):
                    variants.load_variants(self.root)

    def test_rejects_invalid_definitions(self):
        definition = self.definitions["brown"]
        for value in (None, [], "brown", {},
                      {k: v for k, v in definition.items() if k != "sidebar_hover"},
                      dict(definition, unexpected="value")):
            with self.subTest(value=value):
                self.write_variants({"brown": value})
                with self.assertRaisesRegex(ValueError, "Invalid variant definition"):
                    variants.load_variants(self.root)

    def test_rejects_invalid_theme_names(self):
        for name in ("Viparu", "Other-Brown", "Viparu-../Brown", "Viparu-Brown/escape",
                     "Viparu-Brown Theme", "Viparu-Brown\n", "Viparu--Brown", "", None, 1):
            with self.subTest(name=name):
                self.write_variants({"brown": dict(self.definitions["brown"], name=name)})
                with self.assertRaisesRegex(ValueError, "Invalid theme name"):
                    variants.load_variants(self.root)

    def test_rejects_unknown_or_unsafe_palette_references(self):
        for role in PALETTE_ROLES:
            for color in ("missing_color", "$english_walnut", "english-walnut",
                          "rose_taupe;", "linen\n", "LINEN", "#ffffff", "", None,
                          1, 0.5, True, False, [], {}):
                with self.subTest(role=role, color=color):
                    definition = dict(self.definitions["brown"], **{role: color})
                    self.write_variants({"brown": definition})
                    with self.assertRaisesRegex(ValueError, "Unknown palette color"):
                        variants.load_variants(self.root)

    def fixture_definition(self, **options):
        return dict(name="Viparu-Fixture", sidebar_base="linen", sidebar_hover="silver",
                    **options)

    def test_optional_mapping_fixtures_and_removal_do_not_leave_stale_roles(self):
        minimal = self.fixture_definition()
        for option, roles in OPTIONAL_MAPPINGS.items():
            with self.subTest(option=option):
                self.write_variants({"nile-blue": dict(minimal, **{option: "carmine"})})
                variants.generate_variant(self.root)
                expected = {"gp-sidebar-base": "$linen", "gp-sidebar-hover-color": "$silver"}
                expected.update({role: "$carmine" for role in roles})
                self.assertEqual(scss_assignments(self.root), expected)
                self.write_variants({"nile-blue": minimal})
                variants.generate_variant(self.root)
                self.assertEqual(scss_assignments(self.root), {
                    "gp-sidebar-base": "$linen", "gp-sidebar-hover-color": "$silver"})

    def test_sidebar_tint_is_twenty_percent_not_eighty_percent(self):
        self.write_variants({"nile-blue": self.fixture_definition(sidebar_tint="carmine")})
        variants.generate_variant(self.root)
        self.assertEqual(scss_assignments(self.root), {
            "gp-sidebar-base": "mix($linen, $carmine, 80%)",
            "gp-sidebar-hover-color": "$silver"})

    def test_swap_content_surfaces_accepts_both_booleans(self):
        for value in (True, False):
            with self.subTest(value=value):
                self.write_variants({"nile-blue": self.fixture_definition(swap_content_surfaces=value)})
                self.assertIs(variants.load_variants(self.root)["nile-blue"]["swap_content_surfaces"], value)
                variants.generate_variant(self.root)
                self.assertEqual(scss_assignments(self.root), {
                    "gp-sidebar-base": "$linen", "gp-sidebar-hover-color": "$silver",
                    "gp-swap-content-surfaces": "true" if value else "false"})

    def test_swap_content_surfaces_rejects_nonbooleans(self):
        for value in (None, 0, 1, 0.0, "true", "false", "", [], {}):
            with self.subTest(value=value):
                self.write_variants({"nile-blue": self.fixture_definition(swap_content_surfaces=value)})
                with self.assertRaisesRegex(ValueError, "swap_content_surfaces must be a boolean"):
                    variants.load_variants(self.root)

    def test_rejects_duplicate_theme_names(self):
        definitions = {key: dict(value) for key, value in self.definitions.items()}
        definitions["brown"]["name"] = definitions["nile-blue"]["name"]
        self.write_variants(definitions)
        with self.assertRaisesRegex(ValueError, "Duplicate theme name"):
            variants.load_variants(self.root)

    def test_unknown_selection_and_copy_rejected_without_writes(self):
        target = self.directory / "invalid-output"
        with self.assertRaisesRegex(ValueError, "Unknown theme variant"):
            variants.copy_project(target, "unknown", self.root)
        self.assertFalse(target.exists())
        (self.root / "theme-variant").write_text("unknown\n", encoding="utf-8")
        before = (self.root / "index.theme").read_bytes()
        with self.assertRaisesRegex(ValueError, "Unknown selected theme variant"):
            variants.selected_variant(self.root)
        with self.assertRaisesRegex(ValueError, "Unknown selected theme variant"):
            variants.generate_variant(self.root)
        self.assertEqual((self.root / "index.theme").read_bytes(), before)

    def test_copy_excludes_private_directories_and_preserves_active_selector(self):
        for relative in (".git", ".build-tools", "dist", "gnome-shell/.build",
                         "scripts/__pycache__", "scss/.private/nested"):
            path = self.root / relative
            path.mkdir(parents=True, exist_ok=True)
            (path / "private.txt").write_text("private", encoding="utf-8")
        for relative in ("scripts/cache.pyc", "scripts/cache.pyo", "scss/.secret"):
            (self.root / relative).write_text("private", encoding="utf-8")
        selector = (self.root / "theme-variant").read_bytes()
        target = self.directory / "brown-copy"
        expected = {path.relative_to(self.root) for path in variants.project_files(self.root)}
        variants.copy_project(target, "brown", self.root)
        actual = {path.relative_to(target) for path in target.rglob("*") if path.is_file()}
        self.assertEqual(actual, expected)
        self.assertFalse(any("private" in path.parts or any(
            part.startswith(".") or part == "__pycache__" for part in path.parts)
            for path in actual))
        self.assertFalse(any(path.suffix in (".pyc", ".pyo") for path in actual))
        self.assertEqual((target / "theme-variant").read_text(), "brown\n")
        self.assertEqual((self.root / "theme-variant").read_bytes(), selector)
        for path in expected - {Path("theme-variant")}:
            self.assertEqual((target / path).read_bytes(), (self.root / path).read_bytes())

    def test_standalone_builds_stage_variants_without_changing_checkout(self):
        before = {path: (self.root / path).read_bytes() for path in
                  ("theme-variant", "index.theme", "scss/_variant.scss", "gtk-4.0/gtk.css")}

        def mock_build(theme, compiler, environment):
            self.assertEqual(compiler, "mock-sassc")
            self.assertEqual(environment, {"MOCK": "1"})
            variants.generate_variant(theme)
            key, _ = variants.selected_variant(theme)
            (theme / "gtk-4.0/gtk.css").write_text(f"/* mocked {key} */\n", encoding="utf-8")

        with patch.object(builder, "ROOT", self.root), \
                patch.object(builder, "compiler_command", return_value=("mock-sassc", {"MOCK": "1"})), \
                patch.object(builder, "build", side_effect=mock_build) as build:
            outputs = builder.build_variants()
            self.assertEqual(build.call_count, len(self.definitions))
            self.assertEqual(outputs, [self.root / "dist/themes" / value["name"]
                                       for value in self.definitions.values()])
            for key, theme in zip(self.definitions, outputs):
                self.assertEqual(variants.selected_variant(theme), (key, self.definitions[key]))
                self.assertEqual((theme / "gtk-4.0/gtk.css").read_text(), f"/* mocked {key} */\n")
            build.reset_mock()
            self.assertEqual(builder.build_variants(["brown"]),
                             [self.root / "dist/themes/Viparu-Brown"])
            build.assert_called_once()
        for path, content in before.items():
            self.assertEqual((self.root / path).read_bytes(), content)

    def test_unknown_build_variant_rejected_before_compiler(self):
        with patch.object(builder, "ROOT", self.root), \
                patch.object(builder, "compiler_command") as compiler, \
                patch.object(builder, "build") as build:
            with self.assertRaisesRegex(ValueError, "Unknown theme variant"):
                builder.build_variants(["brown", "unknown"])
            compiler.assert_not_called()
            build.assert_not_called()
        self.assertFalse((self.root / "dist").exists())


if __name__ == "__main__":
    unittest.main()
