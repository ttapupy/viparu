"""Shared offscreen GTK fixtures, isolated from the user's installed theme."""

import importlib
import unittest
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STYLESHEETS = ("gtk.css", "libadwaita.css")
SCHEMES = ("FORCE_LIGHT", "FORCE_DARK")


class GtkTestCase(unittest.TestCase):
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

    def setUp(self):
        self.manager = self.Adw.StyleManager.get_default()
        self.addCleanup(self.manager.set_color_scheme, self.manager.get_color_scheme())
        settings = self.Gtk.Settings.get_default()
        self.addCleanup(settings.set_property, "gtk-enable-animations",
                        settings.get_property("gtk-enable-animations"))
        settings.set_property("gtk-enable-animations", False)
        self.renderer = None
        # A higher-priority native baseline masks desktop/user CSS without
        # changing GTK settings, installed files or application visibility.
        self.display = self.Gdk.Display.get_default()
        native = self.Gtk.CssProvider()
        native.load_from_resource("/org/gnome/Adwaita/styles/gtk.css")
        self.Gtk.StyleContext.add_provider_for_display(
            self.display, native, self.Gtk.STYLE_PROVIDER_PRIORITY_USER + 1)
        self.addCleanup(self.Gtk.StyleContext.remove_provider_for_display, self.display, native)
        roles = ("view-fg-color", "view-bg-color", "sidebar-fg-color", "sidebar-bg-color",
                 "headerbar-bg-color", "accent-bg-color", "accent-fg-color", "gp-selection-bg",
                 "gp-selection-fg", "gp-selection-hover-bg", "gp-control-accent-bg",
                 "gp-control-accent-fg", "gp-control-accent-hover-bg", "gp-control-hover-bg")
        reference = self.Gtk.CssProvider()
        reference.load_from_data("\n".join(
            f"label.gp-test-{role} {{ color: var(--{role}); }}" for role in roles).encode())
        self.Gtk.StyleContext.add_provider_for_display(
            self.display, reference, self.Gtk.STYLE_PROVIDER_PRIORITY_USER + 4)
        self.addCleanup(self.Gtk.StyleContext.remove_provider_for_display, self.display, reference)

    @contextmanager
    def themed_window(self, stylesheet, scheme):
        self.manager.set_color_scheme(getattr(self.Adw.ColorScheme, scheme))
        provider = None
        if stylesheet is not None:
            provider = self.Gtk.CssProvider()
            provider.load_from_path(str(ROOT / "gtk-4.0" / stylesheet))
            self.Gtk.StyleContext.add_provider_for_display(
                self.display, provider, self.Gtk.STYLE_PROVIDER_PRIORITY_USER + 3)
        window = self.Gtk.Window()
        content = self.Gtk.Box(orientation=self.Gtk.Orientation.VERTICAL)
        window.set_child(content)
        try:
            yield window, content
        finally:
            visible, mapped = window.get_visible(), window.get_mapped()
            window.destroy()
            if provider is not None:
                self.Gtk.StyleContext.remove_provider_for_display(self.display, provider)
            self.assertFalse(visible, "Tests must never show a window")
            self.assertFalse(mapped, "Tests must never map a window")

    def states(self):
        flags = self.Gtk.StateFlags
        return (
            ("normal", flags.NORMAL), ("focus", flags.FOCUSED | flags.FOCUS_VISIBLE),
            ("hover", flags.PRELIGHT), ("active", flags.PRELIGHT | flags.ACTIVE),
            ("backdrop", flags.BACKDROP), ("backdrop-hover", flags.BACKDROP | flags.PRELIGHT),
            ("backdrop-active", flags.BACKDROP | flags.PRELIGHT | flags.ACTIVE),
        )

    def set_state(self, window, widget, state):
        flags = self.Gtk.StateFlags
        window.unset_state_flags(flags.BACKDROP)
        widget.unset_state_flags(flags.BACKDROP | flags.PRELIGHT | flags.ACTIVE
                                 | flags.FOCUSED | flags.FOCUS_VISIBLE | flags.INSENSITIVE)
        window.set_state_flags(state & flags.BACKDROP, False)
        # CHECKED and SELECTED describe the fixture, not simulated pointer state.
        widget.set_state_flags(state, False)

    def descendants(self, widget):
        yield widget
        child = widget.get_first_child()
        while child is not None:
            yield from self.descendants(child)
            child = child.get_next_sibling()

    @staticmethod
    def edges(border):
        return border.top, border.right, border.bottom, border.left

    def geometry(self, widget):
        context = widget.get_style_context()
        return (
            self.edges(context.get_padding()), self.edges(context.get_border()),
            self.edges(context.get_margin()),
            tuple(tuple(widget.measure(axis, -1)) for axis in
                  (self.Gtk.Orientation.HORIZONTAL, self.Gtk.Orientation.VERTICAL)),
        )

    @staticmethod
    def foreground(widget):
        color = widget.get_color()
        return tuple(round(c * 255) for c in (color.red, color.green, color.blue, color.alpha))

    def role_color(self, content, role):
        label = self.Gtk.Label(css_classes=["gp-test-" + role], visible=False)
        content.append(label)
        try:
            return self.foreground(label)
        finally:
            content.remove(label)

    def paint(self, widget, part="background", width=96, height=48):
        snapshot = self.Gtk.Snapshot()
        getattr(snapshot, "render_" + part)(widget.get_style_context(), 0, 0, width, height)
        return snapshot.to_node()

    def pixels(self, node, width=96, height=48):
        if node is None:
            return [(0, 0, 0, 0)] * (width * height)
        if self.renderer is None:
            self.renderer = self.Gsk.CairoRenderer.new()
            self.assertTrue(self.renderer.realize(None))
            self.addCleanup(self.renderer.unrealize)
        bounds = self.Graphene.Rect()
        bounds.init(0, 0, width, height)
        downloader = self.Gdk.TextureDownloader.new(self.renderer.render_texture(node, bounds))
        downloader.set_format(self.Gdk.MemoryFormat.R8G8B8A8)
        data, stride = downloader.download_bytes()
        data = data.get_data()
        return [tuple(data[y * stride + x * 4:y * stride + x * 4 + 4])
                for y in range(height) for x in range(width)]

    def background(self, widget):
        return self.pixels(self.paint(widget))[24 * 96 + 48]

    def assert_color_close(self, actual, expected, tolerance=2):
        self.assertTrue(all(abs(a - b) <= tolerance for a, b in zip(actual, expected)),
                        f"{actual} is not within {tolerance} of {expected}")
