"""Exercise the GTK cascade and offscreen paint, never presenting a window."""

import importlib
import itertools
import json
import unittest
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STYLESHEETS = ("gtk.css", "libadwaita.css")
SCHEMES = ("FORCE_LIGHT", "FORCE_DARK")


class ControlsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            gi = importlib.import_module("gi")
            gi.require_version("Gtk", "4.0")
            gi.require_version("Adw", "1")
            cls.Gtk = importlib.import_module("gi.repository.Gtk")
            cls.Adw = importlib.import_module("gi.repository.Adw")
            cls.Gdk = importlib.import_module("gi.repository.Gdk")
            cls.Gsk = importlib.import_module("gi.repository.Gsk")
            cls.Graphene = importlib.import_module("gi.repository.Graphene")
        except (ImportError, ValueError) as error:
            raise unittest.SkipTest("GTK 4/libadwaita PyGObject is unavailable") from error
        if (cls.Gtk.get_major_version(), cls.Gtk.get_minor_version()) < (4, 16):
            raise unittest.SkipTest("The theme's CSS variables require GTK 4.16+")
        if not cls.Gtk.init_check() or cls.Gdk.Display.get_default() is None:
            raise unittest.SkipTest("No GTK display is available")
        cls.Adw.init()
        cls.palette = json.loads((ROOT / "color-palette.json").read_text(encoding="utf-8"))

    def setUp(self):
        self.manager = self.Adw.StyleManager.get_default()
        self.addCleanup(self.manager.set_color_scheme, self.manager.get_color_scheme())
        settings = self.Gtk.Settings.get_default()
        self.addCleanup(settings.set_property, "gtk-enable-animations",
                        settings.get_property("gtk-enable-animations"))
        # These are process-local overrides, not writes to desktop GSettings.
        settings.set_property("gtk-enable-animations", False)
        self.renderer = None

    @contextmanager
    def themed_window(self, stylesheet, scheme):
        self.manager.set_color_scheme(getattr(self.Adw.ColorScheme, scheme))
        provider = self.Gtk.CssProvider()
        provider.load_from_path(str(ROOT / "gtk-4.0" / stylesheet))
        display = self.Gdk.Display.get_default()
        # Override any locally installed user CSS without disabling Adwaita's
        # application-level rules: those competing rules caused the regression.
        self.Gtk.StyleContext.add_provider_for_display(
            display, provider, self.Gtk.STYLE_PROVIDER_PRIORITY_USER + 1)
        window = self.Gtk.Window()
        try:
            self.assertFalse(window.get_visible())
            yield window
        finally:
            window.destroy()
            self.Gtk.StyleContext.remove_provider_for_display(display, provider)

    def states(self):
        flags = self.Gtk.StateFlags
        return (
            ("normal", flags.NORMAL),
            ("focus", flags.FOCUSED | flags.FOCUS_VISIBLE),
            ("hover", flags.PRELIGHT),
            ("active", flags.PRELIGHT | flags.ACTIVE),
            ("backdrop", flags.BACKDROP),
            ("backdrop-hover", flags.BACKDROP | flags.PRELIGHT),
            ("backdrop-active", flags.BACKDROP | flags.PRELIGHT | flags.ACTIVE),
        )

    def set_state(self, window, widget, state):
        flags = self.Gtk.StateFlags
        window.unset_state_flags(flags.BACKDROP)
        widget.unset_state_flags(flags.BACKDROP | flags.PRELIGHT | flags.ACTIVE
                                 | flags.FOCUSED | flags.FOCUS_VISIBLE)
        window.set_state_flags(state & flags.BACKDROP, False)
        # Do not clear semantic flags such as CHECKED and SELECTED.
        widget.set_state_flags(state, False)

    def color(self, name):
        value = self.palette[name]
        return tuple(int(value[offset:offset + 2], 16) for offset in (1, 3, 5)) + (255,)

    def assert_foreground(self, widget, name):
        rgba = widget.get_color()
        actual = tuple(round(channel * 255) for channel in
                       (rgba.red, rgba.green, rgba.blue, rgba.alpha))
        self.assertEqual(actual, self.color(name), widget.get_css_name())

    def pixels(self, node, width, height):
        self.assertIsNotNone(node, "Expected an offscreen CSS render node")
        if self.renderer is None:
            self.renderer = self.Gsk.CairoRenderer.new()
            self.assertTrue(self.renderer.realize(None))
            self.addCleanup(self.renderer.unrealize)
        bounds = self.Graphene.Rect()
        bounds.init(0, 0, width, height)
        texture = self.renderer.render_texture(node, bounds)
        downloader = self.Gdk.TextureDownloader.new(texture)
        downloader.set_format(self.Gdk.MemoryFormat.R8G8B8A8)
        data, stride = downloader.download_bytes()
        data = data.get_data()
        return [tuple(data[y * stride + x * 4:y * stride + x * 4 + 4])
                for y in range(height) for x in range(width)]

    def background(self, widget):
        # GTK4 has no computed background-color getter. Snapshot the real CSS
        # background instead; this also includes any inherited bitmap/SVG image.
        snapshot = self.Gtk.Snapshot()
        snapshot.render_background(widget.get_style_context(), 0, 0, 80, 40)
        node = snapshot.to_node()
        self.assertIsNotNone(node, "Missing painted background for " + widget.get_css_name())
        self.assertNotIn(b"texture", node.serialize().get_data(),
                         "A legacy image still paints the control background")
        return self.pixels(node, 80, 40)[20 * 80 + 40]

    def descendants(self, widget):
        yield widget
        child = widget.get_first_child()
        while child is not None:
            yield from self.descendants(child)
            child = child.get_next_sibling()

    def test_sidebar_labels_and_selection(self):
        Gtk = self.Gtk
        for stylesheet, scheme in itertools.product(STYLESHEETS, SCHEMES):
            for kind in ("sidebar", "navigation-sidebar", "stacksidebar"):
                with self.subTest(css=stylesheet, scheme=scheme, sidebar=kind), \
                        self.themed_window(stylesheet, scheme) as window:
                    if kind == "stacksidebar":
                        stack = Gtk.Stack()
                        stack.add_titled(Gtk.Box(), "appearance", "Appearance")
                        stack.add_titled(Gtk.Box(), "keyboard", "Keyboard & Mouse")
                        sidebar = Gtk.StackSidebar(stack=stack)
                        content = Gtk.Box()
                        content.append(sidebar)
                        content.append(stack)
                        window.set_child(content)
                        rows = [widget for widget in self.descendants(sidebar)
                                if isinstance(widget, Gtk.ListBoxRow)]
                        row, other = rows
                        label = row.get_child()
                    else:
                        sidebar = Gtk.ListBox()
                        sidebar.add_css_class(kind)
                        label = Gtk.Label(label="Keyboard & Mouse")
                        row = Gtk.ListBoxRow()
                        row.set_child(label)
                        sidebar.append(row)
                        other = Gtk.ListBoxRow(child=Gtk.Label(label="Appearance"))
                        sidebar.append(other)
                        window.set_child(sidebar)
                    for selected in (False, True):
                        if kind == "stacksidebar":
                            sidebar.get_stack().set_visible_child_name(
                                "appearance" if selected else "keyboard")
                        else:
                            sidebar.select_row(row if selected else other)
                        self.assertEqual(row.is_selected(), selected)
                        for state_name, state in self.states():
                            with self.subTest(selected=selected, state=state_name):
                                self.set_state(window, row, state)
                                self.assert_foreground(label, "almost_black" if selected else "linen")
                                if selected:
                                    color = "light_orange" if state & Gtk.StateFlags.PRELIGHT else "warm_orange"
                                    self.assertEqual(self.background(row), self.color(color))

    def test_checked_linked_toggle_label_on_ocean_blue(self):
        Gtk = self.Gtk
        for stylesheet, scheme in itertools.product(STYLESHEETS, SCHEMES):
            with self.subTest(css=stylesheet, scheme=scheme), \
                    self.themed_window(stylesheet, scheme) as window:
                # Tweaks puts the segmented control inside a light list row;
                # checking only the button's own foreground misses black labels.
                listing = Gtk.ListBox()
                listing.add_css_class("boxed-list")
                row = Gtk.ListBoxRow()
                linked = Gtk.Box()
                linked.add_css_class("linked")
                button = Gtk.ToggleButton(label="Left")
                button.set_active(True)
                linked.append(button)
                linked.append(Gtk.ToggleButton(label="Right"))
                row.set_child(linked)
                listing.append(row)
                window.set_child(listing)
                for state_name, state in self.states():
                    with self.subTest(state=state_name):
                        self.set_state(window, button, state)
                        self.assertTrue(button.get_active())
                        self.assert_foreground(button.get_child(), "white")
                        color = "petrol_blue" if state & Gtk.StateFlags.PRELIGHT else "french_blue"
                        self.assertEqual(self.background(button), self.color(color))

    def test_linked_toggle_size_does_not_change_when_checked(self):
        Gtk = self.Gtk
        for stylesheet, scheme in itertools.product(STYLESHEETS, SCHEMES):
            with self.subTest(css=stylesheet, scheme=scheme), \
                    self.themed_window(stylesheet, scheme) as window:
                linked = Gtk.Box(css_classes=["linked"])
                button = Gtk.ToggleButton(label="Bal startgomb")
                linked.append(button)
                linked.append(Gtk.ToggleButton(label="Jobb startgomb"))
                window.set_child(linked)
                linked.allocate(500, 60, -1, None)
                first_ok, first_bounds = button.compute_bounds(linked)
                second_ok, second_bounds = linked.get_last_child().compute_bounds(linked)
                self.assertTrue(first_ok and second_ok)
                gap = second_bounds.get_x() - first_bounds.get_x() - first_bounds.get_width()
                self.assertGreaterEqual(gap, 6)
                for state_name, state in self.states():
                    with self.subTest(state=state_name):
                        measurements = []
                        for checked in (False, True):
                            button.set_active(checked)
                            self.set_state(window, button, state)
                            measurements.append(tuple(
                                tuple(button.measure(axis, -1))
                                for axis in (Gtk.Orientation.HORIZONTAL, Gtk.Orientation.VERTICAL)
                            ))
                        self.assertEqual(measurements[0], measurements[1])

    def test_switch_trough_and_thumb_are_palette_painted(self):
        Gtk = self.Gtk
        for stylesheet, scheme in itertools.product(STYLESHEETS, SCHEMES):
            with self.subTest(css=stylesheet, scheme=scheme), \
                    self.themed_window(stylesheet, scheme) as window:
                switch = Gtk.Switch()
                window.set_child(switch)
                slider = next(widget for widget in self.descendants(switch)
                              if widget.get_css_name() == "slider")
                for checked in (False, True):
                    switch.set_active(checked)
                    switch.set_state(checked)
                    for state_name, state in self.states():
                        with self.subTest(checked=checked, state=state_name):
                            self.set_state(window, switch, state)
                            self.set_state(window, slider, state)
                            trough = self.background(switch)
                            if checked:
                                self.assertEqual(trough, self.color("french_blue"))
                            else:
                                # The off-state role may choose either warm gray
                                # or a muted blend, but never an accent/green asset.
                                red, green, blue, alpha = trough
                                self.assertEqual(alpha, 255)
                                self.assertLessEqual(max(trough[:3]) - min(trough[:3]), 40)
                                self.assertGreaterEqual(red, blue)
                                self.assertGreaterEqual(min(red, green, blue), 60)
                                self.assertLess(max(red, green, blue), 235)
                            thumb = self.background(slider)
                            if checked:
                                self.assertEqual(thumb, self.color("white"))

    def test_check_and_radio_indicators_use_selection_palette(self):
        Gtk = self.Gtk
        for stylesheet, scheme in itertools.product(STYLESHEETS, SCHEMES):
            for kind in ("check", "radio"):
                with self.subTest(css=stylesheet, scheme=scheme, indicator=kind), \
                        self.themed_window(stylesheet, scheme) as window:
                    box = Gtk.Box()
                    button = Gtk.CheckButton()
                    box.append(button)
                    if kind == "radio":
                        peer = Gtk.CheckButton()
                        box.append(peer)
                        button.set_group(peer)
                    button.set_active(True)
                    window.set_child(box)
                    indicator = button.get_first_child()
                    self.assertEqual(indicator.get_css_name(), kind)
                    # Allocation, not realization/mapping, gives the builtin
                    # indicator its dimensions for its foreground snapshot vfunc.
                    button.allocate(48, 32, -1, None)
                    for state_name, state in self.states():
                        with self.subTest(state=state_name):
                            self.set_state(window, button, state)
                            self.set_state(window, indicator, state)
                            self.assert_foreground(indicator, "almost_black")
                            self.assertEqual(self.background(indicator), self.color("warm_orange"))
                            width, height = indicator.get_width(), indicator.get_height()
                            self.assertGreater(min(width, height), 0)
                            snapshot = Gtk.Snapshot()
                            context = indicator.get_style_context()
                            snapshot.render_background(context, 0, 0, width, height)
                            snapshot.render_frame(context, 0, 0, width, height)
                            type(indicator).do_snapshot(indicator, snapshot)
                            pixels = self.pixels(snapshot.to_node(), width, height)
                            fill, ink = self.color("warm_orange"), self.color("almost_black")
                            self.assertIn(fill, pixels)
                            self.assertIn(ink, pixels, "The selected glyph/dot must actually paint the foreground")
                            # Away from borders, only selection colors and their
                            # antialiased mixtures are valid, not old green PNGs.
                            unexpected = set()
                            for y in range(height // 4, height - height // 4):
                                for x in range(width // 4, width - width // 4):
                                    pixel = pixels[y * width + x]
                                    mix = (pixel[0] - fill[0]) / (ink[0] - fill[0])
                                    if pixel[3] != 255 or not all(
                                            abs(pixel[c] - (fill[c] + mix * (ink[c] - fill[c]))) <= 4
                                            for c in (1, 2)):
                                        unexpected.add(pixel)
                            self.assertFalse(unexpected, f"Non-palette indicator pixels: {unexpected}")


if __name__ == "__main__":
    unittest.main()
