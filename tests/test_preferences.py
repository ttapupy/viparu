"""Rooted, never-presented GTK preferences regressions against both built outputs.

Popup states are simulated; these tests do not open popovers or drive input.
"""

import importlib
import itertools
import json
import unittest
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STYLESHEETS = ("gtk.css",)
SCHEMES = ("FORCE_LIGHT", "FORCE_DARK")
ROLES = {
    "hover": "--gp-control-hover-bg",
    "active": "--gp-control-active-bg",
    "control": "--gp-control-bg",
    "foreground": "--view-fg-color",
    "muted": "--gp-muted-fg",
    "selection": "--gp-selection-bg",
    "selection-hover": "--gp-selection-hover-bg",
    "selection-foreground": "--gp-selection-fg",
}


class PreferencesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            gi = importlib.import_module("gi")
            gi.require_version("Gtk", "4.0")
            gi.require_version("Adw", "1")
            for name in ("Gtk", "Adw", "Gdk", "Gsk", "Graphene"):
                setattr(cls, name, importlib.import_module("gi.repository." + name))
        except (ImportError, ValueError) as error:
            raise unittest.SkipTest("GTK 4/libadwaita PyGObject is unavailable") from error
        if (cls.Gtk.get_major_version(), cls.Gtk.get_minor_version()) < (4, 16):
            raise unittest.SkipTest("CSS variables require GTK 4.16+")
        if not hasattr(cls.Gdk, "TextureDownloader"):
            raise unittest.SkipTest("Gdk.TextureDownloader is unavailable")
        if not cls.Gtk.init_check() or cls.Gdk.Display.get_default() is None:
            raise unittest.SkipTest("No GTK display is available")
        cls.Adw.init()
        palette = json.loads((ROOT / "color-palette.json").read_text(encoding="utf-8"))
        coral = palette["carmine"]
        cls.focus_color = tuple(int(coral[i:i + 2], 16) for i in (1, 3, 5)) + (255,)

    def setUp(self):
        manager = self.Adw.StyleManager.get_default()
        self.addCleanup(manager.set_color_scheme, manager.get_color_scheme())
        settings = self.Gtk.Settings.get_default()
        self.addCleanup(settings.set_property, "gtk-enable-animations",
                        settings.get_property("gtk-enable-animations"))
        # Process-local GTK overrides only; never desktop GSettings writes.
        settings.set_property("gtk-enable-animations", False)
        self.renderer = None

    @contextmanager
    def themed_window(self, stylesheet, scheme):
        Gtk = self.Gtk
        self.Adw.StyleManager.get_default().set_color_scheme(
            getattr(self.Adw.ColorScheme, scheme))
        display = self.Gdk.Display.get_default()
        theme = Gtk.CssProvider()
        theme.load_from_path(str(ROOT / "gtk-4.0" / stylesheet))
        reference = Gtk.CssProvider()
        reference.load_from_data("\n".join(
            f"label.gp-preferences-{name} {{ color: var({variable}); }}"
            for name, variable in ROLES.items()).encode())
        Gtk.StyleContext.add_provider_for_display(
            display, theme, Gtk.STYLE_PROVIDER_PRIORITY_USER + 1)
        Gtk.StyleContext.add_provider_for_display(
            display, reference, Gtk.STYLE_PROVIDER_PRIORITY_USER + 2)
        window = Gtk.Window()
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        window.set_child(content)
        try:
            yield window, content
        finally:
            visible, mapped = window.get_visible(), window.get_mapped()
            window.destroy()
            Gtk.StyleContext.remove_provider_for_display(display, reference)
            Gtk.StyleContext.remove_provider_for_display(display, theme)
            self.assertFalse(visible, "Tests must never show a window")
            self.assertFalse(mapped, "Tests must never map a window")

    def descendants(self, widget):
        yield widget
        child = widget.get_first_child()
        while child is not None:
            yield from self.descendants(child)
            child = child.get_next_sibling()

    @staticmethod
    def edges(border):
        return (border.top, border.right, border.bottom, border.left)

    @staticmethod
    def foreground(widget):
        color = widget.get_color()
        return tuple(round(c * 255) for c in
                     (color.red, color.green, color.blue, color.alpha))

    def role_color(self, content, role):
        label = self.Gtk.Label(css_classes=["gp-preferences-" + role], visible=False)
        content.append(label)
        return self.foreground(label)

    def set_state(self, widget, flags):
        state = self.Gtk.StateFlags
        widget.unset_state_flags(state.PRELIGHT | state.ACTIVE | state.FOCUSED
                                 | state.FOCUS_VISIBLE | state.BACKDROP | state.INSENSITIVE)
        widget.set_state_flags(flags, False)

    def paint(self, widget, part="background"):
        snapshot = self.Gtk.Snapshot()
        getattr(snapshot, "render_" + part)(widget.get_style_context(), 0, 0, 96, 48)
        return snapshot.to_node()

    def pixels(self, node):
        if node is None:
            return [(0, 0, 0, 0)] * (96 * 48)
        if self.renderer is None:
            self.renderer = self.Gsk.CairoRenderer.new()
            self.assertTrue(self.renderer.realize(None))
            self.addCleanup(self.renderer.unrealize)
        bounds = self.Graphene.Rect()
        bounds.init(0, 0, 96, 48)
        downloader = self.Gdk.TextureDownloader.new(
            self.renderer.render_texture(node, bounds))
        downloader.set_format(self.Gdk.MemoryFormat.R8G8B8A8)
        data, stride = downloader.download_bytes()
        data = data.get_data()
        return [tuple(data[y * stride + x * 4:y * stride + x * 4 + 4])
                for y in range(48) for x in range(96)]

    def background(self, widget):
        return self.pixels(self.paint(widget))[24 * 96 + 48]

    def assert_focus_ring(self, widget):
        node = self.paint(widget, "focus")
        self.assertIsNotNone(node, "The keyboard focus outline disappeared")
        self.assertRegex(node.serialize().get_data().decode(), r"widths:\s*2(?:\s+2){0,3};")
        self.assertIn(self.focus_color, self.pixels(node), "Focus must actually paint coral")

    def combo_group(self, content):
        group = self.Adw.PreferencesGroup()
        content.append(group)
        first = self.Adw.ActionRow(title="First", activatable=True)
        row = self.Adw.ComboRow(
            title="Új ikonok helyzete", subtitle="A következő új ikon helye",
            model=self.Gtk.StringList.new(["Balra fent", "Jobbra lent"]), selected=1)
        last = self.Adw.ActionRow(title="Last", activatable=True)
        for item in (first, row, last):
            group.add(item)
        return first, row, last

    def test_combo_inline_geometry_row_states_and_card_corners(self):
        Gtk = self.Gtk
        flags = Gtk.StateFlags
        for stylesheet, scheme in itertools.product(STYLESHEETS, SCHEMES):
            with self.subTest(css=stylesheet, scheme=scheme), \
                    self.themed_window(stylesheet, scheme) as (window, content):
                first, row, last = self.combo_group(content)
                window.allocate(640, 260, -1, None)
                inline = next(w for w in self.descendants(row)
                              if isinstance(w, Gtk.ListView) and w.has_css_class("inline"))
                item = inline.get_first_child()
                value = next(w for w in self.descendants(inline) if isinstance(w, Gtk.Label))
                self.assertEqual(value.get_text(), "Jobbra lent")
                self.assertFalse(value.get_selectable())
                self.assertFalse(item.get_state_flags() & flags.SELECTED)
                self.assertEqual(self.edges(item.get_style_context().get_padding()), (2, 2, 2, 2))
                self.assertEqual(self.edges(inline.get_style_context().get_border()), (0, 0, 0, 0))
                self.assertGreaterEqual(inline.get_height(), value.get_height() + 4)
                self.assertTrue(all(p >= 2 for p in self.edges(row.get_style_context().get_padding())))
                title = next(w for w in self.descendants(row)
                             if isinstance(w, Gtk.Label) and w.has_css_class("title"))
                subtitle = next(w for w in self.descendants(row)
                                if isinstance(w, Gtk.Label) and w.has_css_class("subtitle"))
                self.assertEqual(self.foreground(title), self.role_color(content, "foreground"))
                self.assertEqual(self.foreground(subtitle), self.role_color(content, "muted"))
                for name, state in (
                    ("normal", flags.NORMAL), ("hover", flags.PRELIGHT),
                    ("active", flags.PRELIGHT | flags.ACTIVE),
                    ("focus", flags.FOCUSED | flags.FOCUS_VISIBLE),
                    ("backdrop", flags.BACKDROP),
                    ("backdrop-hover", flags.BACKDROP | flags.PRELIGHT),
                    ("disabled", flags.INSENSITIVE),
                ):
                    with self.subTest(state=name):
                        self.set_state(row, state)
                        self.assertEqual(self.background(inline)[3], 0)
                        self.assertEqual(self.background(item)[3], 0)
                        if state & flags.ACTIVE:
                            self.assertEqual(self.background(row), self.role_color(content, "active"))
                        elif state & flags.PRELIGHT:
                            self.assertEqual(self.background(row), self.role_color(content, "hover"))
                        if state & flags.FOCUS_VISIBLE:
                            self.assert_focus_ring(row)
                self.set_state(row, flags.PRELIGHT | flags.FOCUSED | flags.FOCUS_VISIBLE)
                row.add_css_class("has-open-popup")
                self.assertEqual(self.background(row), self.role_color(content, "active"))
                self.assertEqual(self.background(inline)[3], 0)
                self.assert_focus_ring(row)
                row.remove_css_class("has-open-popup")
                for outer in (first, last):
                    self.set_state(outer, flags.PRELIGHT)
                # Inherited card corners clip only the first/last outside edges.
                self.assertEqual(self.pixels(self.paint(first))[0][3], 0)
                self.assertEqual(self.pixels(self.paint(last))[-1][3], 0)
                self.assertEqual(self.pixels(self.paint(row))[0][3], 255)

    def test_genuine_dropdown_combo_and_suffix_menu_geometry(self):
        Gtk = self.Gtk
        flags = Gtk.StateFlags
        for stylesheet, scheme, kind in itertools.product(
                STYLESHEETS, SCHEMES, ("dropdown", "combobox", "menubutton")):
            with self.subTest(css=stylesheet, scheme=scheme, control=kind), \
                    self.themed_window(stylesheet, scheme) as (window, content):
                group = self.Adw.PreferencesGroup()
                content.append(group)
                row = self.Adw.ActionRow(title="Placement")
                group.add(row)
                if kind == "dropdown":
                    control = Gtk.DropDown.new_from_strings(["Jobbra lent", "Balra fent"])
                elif kind == "combobox":
                    control = Gtk.ComboBoxText()
                    control.append_text("Jobbra lent")
                    control.set_active(0)
                else:
                    control = Gtk.MenuButton(label="Jobbra lent")
                    control.set_popover(Gtk.Popover(child=Gtk.Label(label="Choices")))
                control.set_valign(Gtk.Align.CENTER)
                row.add_suffix(control)
                window.allocate(640, 140, -1, None)
                button = next(w for w in self.descendants(control) if isinstance(w, Gtk.Button))
                context = button.get_style_context()
                self.assertEqual(self.edges(context.get_padding()), (6, 10, 6, 10))
                self.assertEqual(self.edges(context.get_border()), (1, 1, 1, 1))
                frame = self.paint(button, "frame")
                self.assertIsNotNone(frame)
                self.assertIn("/ 8", frame.serialize().get_data().decode())
                self.assertTrue(any(pixel[3] for pixel in self.pixels(frame)), "Missing contour")
                self.assertEqual(self.background(button), self.role_color(content, "control"))
                for state, role in ((flags.PRELIGHT, "hover"),
                                    (flags.PRELIGHT | flags.ACTIVE, "active"),
                                    (flags.CHECKED, "active")):
                    self.set_state(button, state)
                    self.assertEqual(self.background(button), self.role_color(content, role))
                    button.unset_state_flags(flags.CHECKED)
                self.set_state(button, flags.FOCUSED | flags.FOCUS_VISIBLE)
                self.assert_focus_ring(button)

    def test_combo_popup_selection_without_opening_it(self):
        Gtk = self.Gtk
        flags = Gtk.StateFlags
        for stylesheet, scheme in itertools.product(STYLESHEETS, SCHEMES):
            with self.subTest(css=stylesheet, scheme=scheme), \
                    self.themed_window(stylesheet, scheme) as (window, content):
                _, row, _ = self.combo_group(content)
                window.allocate(640, 260, -1, None)
                popover = next(w for w in self.descendants(row) if isinstance(w, Gtk.Popover))
                listing = next(w for w in self.descendants(popover) if isinstance(w, Gtk.ListView))
                item = listing.get_first_child()
                self.assertIsNotNone(item, "Expected the model's unshown popup list items")
                label = next(w for w in self.descendants(item) if isinstance(w, Gtk.Label))
                item.set_state_flags(flags.SELECTED, False)
                self.assertEqual(self.background(item), self.role_color(content, "selection"))
                self.assertEqual(self.foreground(label), self.role_color(content, "selection-foreground"))
                item.set_state_flags(flags.PRELIGHT | flags.FOCUSED | flags.FOCUS_VISIBLE, False)
                self.assertEqual(self.background(item), self.role_color(content, "selection-hover"))
                self.assert_focus_ring(item)
                self.assertFalse(popover.get_visible())
                self.assertFalse(popover.get_mapped())

    def test_ordinary_file_listview_stays_opaque(self):
        for stylesheet, scheme in itertools.product(STYLESHEETS, SCHEMES):
            with self.subTest(css=stylesheet, scheme=scheme), \
                    self.themed_window(stylesheet, scheme) as (window, content):
                listing = self.Gtk.ListView()
                content.append(listing)
                window.allocate(640, 200, -1, None)
                for state in (self.Gtk.StateFlags.NORMAL, self.Gtk.StateFlags.BACKDROP):
                    self.set_state(listing, state)
                    self.assertEqual(self.background(listing)[3], 255)


if __name__ == "__main__":
    unittest.main()
