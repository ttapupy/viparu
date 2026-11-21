"""Static quick-toggle cascade checks against this checkout/archive's compiled CSS.

ROOT is deliberately not a dist path: the same tests exercise Nile and Brown
when shipped in either package, without a compiler or a running Shell.
"""

import itertools
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
TARGETS = (".quick-toggle", ".quick-toggle-has-menu .quick-toggle-menu-button")


def compiled_rules(css):
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)
    for selectors, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css):
        declarations = []
        for declaration in body.split(";"):
            if ":" in declaration:
                name, value = declaration.split(":", 1)
                declarations.append((name.strip(), value.strip().lower()))
        for selector in selectors.split(","):
            yield selector.strip(), declarations


def toggle_style(rules, target, states):
    """Resolve class/pseudo-class descendant selectors for two fixed fixtures.

    This is intentionally not a Shell/CSS engine. Shell's st-* expressions stay
    unevaluated, so we check their palette inputs and state transforms verbatim.
    """
    classes = {"quick-toggle", "button"} if target == TARGETS[0] else {"quick-toggle-menu-button"}
    winners = {}
    for order, (selector, declarations) in enumerate(rules):
        parts = selector.split()
        if not parts or len(parts) > 2:
            continue
        if len(parts) == 2:
            parent = parts[0]
            if target == TARGETS[0] or parent != ".quick-toggle-has-menu":
                continue
        leaf = parts[-1]
        # Unsupported selector forms must not be silently treated as matches.
        if not re.fullmatch(r"(?:[.:][a-zA-Z0-9_-]+)+", leaf):
            continue
        required_classes = set(re.findall(r"\.([a-zA-Z0-9_-]+)", leaf))
        required_states = set(re.findall(r":([a-zA-Z0-9_-]+)", leaf))
        if not required_classes <= classes or not required_states <= states:
            continue
        specificity = len(re.findall(r"[.:][a-zA-Z0-9_-]+", selector))
        for name, value in declarations:
            important = value.endswith("!important")
            rank = (important, specificity, order)
            if name not in winners or rank >= winners[name][0]:
                winners[name] = rank, value.removesuffix("!important").strip()
    return {name: value for name, (_, value) in winners.items()}


def mix_hex(first, second, weight):
    channels = [int(weight * int(first[i:i + 2], 16)
                    + (1 - weight) * int(second[i:i + 2], 16) + 0.5)
                for i in (1, 3, 5)]
    return "#{:02x}{:02x}{:02x}".format(*channels)


class ShellStateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        key = (ROOT / "theme-variant").read_text(encoding="utf-8").strip()
        cls.variant = json.loads((ROOT / "theme-variants.json").read_text(encoding="utf-8"))[key]
        cls.palette = {key: value.lower() for key, value in
                       json.loads((ROOT / "color-palette.json").read_text(encoding="utf-8")).items()}
        cls.rules = list(compiled_rules(
            (ROOT / "gnome-shell/gnome-shell.css").read_text(encoding="utf-8")))

    def style(self, target, *states):
        result = toggle_style(self.rules, target, set(states))
        self.assertIn("color", result, (target, states))
        self.assertIn("background-color", result, (target, states))
        return result

    def test_quick_toggle_selectors_do_not_use_unsupported_not(self):
        selectors = [selector for selector, _ in self.rules if "quick-toggle" in selector]
        self.assertTrue(selectors)
        for selector in selectors:
            with self.subTest(selector=selector):
                self.assertNotIn(":not(", selector)

    def test_checked_and_unchecked_hover_focus_foregrounds(self):
        for target, checked, interaction in itertools.product(
                TARGETS, (False, True), (("hover",), ("focus",))):
            with self.subTest(target=target, checked=checked, interaction=interaction):
                states = ("checked",) if checked else ()
                normal_role = (self.variant.get("shell_toggle_fg", "almost_black")
                               if checked else "linen")
                focus_role = self.variant.get("shell_toggle_focus_fg", normal_role)
                self.assertEqual(self.style(target, *states)["color"], self.palette[normal_role])
                self.assertEqual(self.style(target, *states, *interaction)["color"],
                                 self.palette[focus_role])

    def test_configured_unchecked_hover_focus_surfaces_are_pale(self):
        if "shell_toggle_focus_fg" not in self.variant:
            # The optional feature must not leak into the default Nile styles.
            pale = mix_hex(self.palette["silver"], self.palette["linen"], 0.7)
            for target in TARGETS:
                for state in ("hover", "focus"):
                    self.assertNotEqual(self.style(target, state)["background-color"], pale)
            return
        pale = mix_hex(self.palette["silver"], self.palette["linen"], 0.7)
        for target, interaction in itertools.product(
                TARGETS, (("hover",), ("focus",))):
            with self.subTest(target=target, interaction=interaction):
                self.assertEqual(self.style(target, *interaction)["background-color"], pale)
                self.assertNotEqual(self.style(target)["background-color"], pale)

    def test_checked_background_preserves_active_accent_instead_of_unchecked_pale(self):
        for target in TARGETS:
            base = self.style(target, "checked")["background-color"]
            if "shell_toggle_bg" in self.variant:
                gold = self.palette[self.variant["shell_toggle_bg"]]
                expected = (gold if target == TARGETS[0]
                            else mix_hex(gold, self.palette["linen"], 0.85))
                self.assertEqual(base, expected)
            for state, function in (("hover", "st-lighten"), ("focus", "st-mix"),
                                    ("active", "st-lighten")):
                with self.subTest(target=target, state=state):
                    background = self.style(target, "checked", state)["background-color"]
                    self.assertIn(base, background)
                    self.assertTrue(background.startswith(function + "("), background)
                    pale = mix_hex(self.palette["silver"], self.palette["linen"], 0.7)
                    self.assertNotEqual(background, pale)

    def test_disabled_hover_focus_cannot_restore_enabled_foreground_or_surface(self):
        if "shell_toggle_focus_fg" not in self.variant:
            self.skipTest("Optional toggle focus override is not configured")
        for target, checked in itertools.product(TARGETS, (False, True)):
            states = ("checked", "insensitive") if checked else ("insensitive",)
            fg = self.palette[self.variant.get("shell_toggle_fg", "almost_black")] if checked else self.palette["linen"]
            # The unchecked menu button has no native insensitive rule. The
            # optional guard intentionally uses the common button's disabled role.
            disabled = self.style(target if checked else TARGETS[0], *states)
            for interaction in ("hover", "focus"):
                with self.subTest(target=target, checked=checked, interaction=interaction):
                    guard = f"{target}{':checked' if checked else ''}:insensitive:{interaction}"
                    self.assertTrue(any(selector == guard for selector, _ in self.rules), guard)
                    actual = self.style(target, *states, interaction)
                    self.assertEqual(actual["color"], f"st-transparentize({fg}, 0.5)")
                    self.assertEqual(actual["background-color"], disabled["background-color"])


if __name__ == "__main__":
    unittest.main()
