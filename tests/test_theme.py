import importlib
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GTK = ROOT / "gtk-4.0"


def asset_urls(path):
    css = re.sub(r"/\*.*?\*/", "", path.read_text(encoding="utf-8"), flags=re.DOTALL)
    return set(re.findall(r"url\(\s*[\"']?([^\"')\s]+)", css))


class ThemeTests(unittest.TestCase):
    def test_dark_variant_is_also_hybrid(self):
        self.assertEqual((GTK / "gtk.css").read_bytes(), (GTK / "gtk-dark.css").read_bytes())

    def test_named_colors_and_css_variables_agree(self):
        css = (GTK / "gtk.css").read_text(encoding="utf-8")
        # Roles are intentionally editable; validate both export APIs without
        # pinning the header/sidebar to a particular experimental palette color.
        for role in ("window_fg_color", "headerbar_bg_color", "sidebar_bg_color", "accent_bg_color"):
            with self.subTest(role=role):
                named = re.search(r"@define-color " + role + r" ([^;]+);", css)
                variable = re.search(r"--" + role.replace("_", "-") + r": ([^;]+);", css)
                self.assertIsNotNone(named)
                self.assertIsNotNone(variable)
                assert named is not None and variable is not None
                self.assertEqual(named.group(1).lower(), variable.group(1).lower())

    def test_window_background_matches_unchanged_file_view(self):
        colors = json.loads((ROOT / "color-palette.json").read_text(encoding="utf-8"))
        channels = [
            round(0.6 * int(colors["white"][offset:offset + 2], 16)
                  + 0.4 * int(colors["linen"][offset:offset + 2], 16))
            for offset in (1, 3, 5)
        ]
        expected = "#{:02x}{:02x}{:02x}".format(*channels)
        for name in ("gtk.css", "gtk-dark.css", "libadwaita.css"):
            css = (GTK / name).read_text(encoding="utf-8")
            for role in ("window_bg_color", "view_bg_color", "dialog_bg_color", "popover_bg_color"):
                with self.subTest(stylesheet=name, role=role):
                    match = re.search(r"@define-color " + role + r" ([^;]+);", css)
                    self.assertIsNotNone(match)
                    assert match is not None
                    self.assertEqual(match.group(1).lower(), expected)
            for role in ("window-bg-color", "view-bg-color", "dialog-bg-color", "popover-bg-color"):
                with self.subTest(stylesheet=name, variable=role):
                    match = re.search(r"--" + role + r": ([^;]+);", css)
                    self.assertIsNotNone(match)
                    assert match is not None
                    self.assertEqual(match.group(1).lower(), expected)

    def test_shell_assets_exist_and_are_local(self):
        path = ROOT / "gnome-shell/gnome-shell.css"
        urls = asset_urls(path)
        self.assertTrue(urls)
        for url in urls:
            with self.subTest(url=url):
                self.assertNotIn("://", url)
                self.assertTrue((path.parent / url).is_file())

    def test_gtk_assets_exist_and_are_local(self):
        for version in ("gtk-3.0", "gtk-4.0"):
            for name in ("gtk.css", "gtk-dark.css"):
                path = ROOT / version / name
                for url in asset_urls(path):
                    with self.subTest(version=version, stylesheet=name, url=url):
                        self.assertNotIn("://", url)
                        self.assertTrue((path.parent / url).is_file())

    def test_shell_accents_are_not_system_dependent(self):
        css = (ROOT / "gnome-shell/gnome-shell.css").read_text(encoding="utf-8")
        css = re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)
        self.assertNotIn("-st-accent-color", css)
        self.assertNotIn("-st-accent-fg-color", css)
        self.assertNotIn("$gp-", css)

    def test_inset_window_outline_stays_rounded_and_darkens_in_backdrop(self):
        try:
            gi = importlib.import_module("gi")
            gi.require_version("Gtk", "4.0")
            gi.require_version("Adw", "1")
            Gtk = importlib.import_module("gi.repository.Gtk")
            Adw = importlib.import_module("gi.repository.Adw")
            Gdk = importlib.import_module("gi.repository.Gdk")
        except (ImportError, ValueError):
            self.skipTest("GTK 4/libadwaita PyGObject is not available")
        if Gtk.get_minor_version() < 16 or not Gtk.init_check():
            self.skipTest("GTK 4.16+ and a display are required")
        Adw.init()
        settings = Gtk.Settings.get_default()
        self.addCleanup(settings.set_property, "gtk-enable-animations",
                        settings.get_property("gtk-enable-animations"))
        settings.set_property("gtk-enable-animations", False)
        display = Gdk.Display.get_default()
        for stylesheet in ("gtk.css", "libadwaita.css"):
            provider = Gtk.CssProvider()
            provider.load_from_path(str(GTK / stylesheet))
            Gtk.StyleContext.add_provider_for_display(
                display, provider, Gtk.STYLE_PROVIDER_PRIORITY_USER + 1)
            try:
                for state in (None, "tiled", "tiled-left", "tiled-right", "tiled-top", "tiled-bottom"):
                    window = Gtk.Window()
                    window.add_css_class("csd")
                    if state:
                        window.add_css_class(state)
                    toolbar = Adw.ToolbarView()
                    header = Gtk.HeaderBar()
                    search = Gtk.ToggleButton(icon_name="system-search-symbolic")
                    reference = Gtk.Button(icon_name="system-search-symbolic")
                    header.pack_start(search)
                    header.pack_end(reference)
                    toolbar.add_top_bar(header)
                    toolbar.set_content(Gtk.Box(vexpand=True))
                    window.set_child(toolbar)
                    window.realize()
                    window.allocate(500, 260, -1, None)
                    try:
                        self.assertFalse(window.get_visible())
                        self.assertFalse(window.get_mapped())
                        self.assertEqual(window.get_allocated_width() - window.get_width(), 0)
                        self.assertEqual(window.get_allocated_height() - window.get_height(), 0)
                        colors = []
                        for inactive in (False, True):
                            with self.subTest(css=stylesheet, state=state, backdrop=inactive):
                                window.unset_state_flags(Gtk.StateFlags.BACKDROP)
                                if inactive:
                                    window.set_state_flags(Gtk.StateFlags.BACKDROP, False)
                                context = window.get_style_context()
                                padding = context.get_padding()
                                self.assertEqual((padding.top, padding.right, padding.bottom, padding.left), (0, 0, 0, 0))
                                border = context.get_border()
                                self.assertEqual((border.top, border.right, border.bottom, border.left), (0, 0, 0, 0))
                                for axis in (Gtk.Orientation.HORIZONTAL, Gtk.Orientation.VERTICAL):
                                    self.assertEqual(tuple(search.measure(axis, -1)),
                                                     tuple(reference.measure(axis, -1)))
                                snapshot = Gtk.Snapshot()
                                snapshot.render_focus(context, 0, 0, 100, 60)
                                node = snapshot.to_node()
                                self.assertIsNotNone(node)
                                serialized = node.serialize().get_data().decode()
                                self.assertRegex(serialized, r"outline: 0 0 100 60 /\s*[1-9]")
                                self.assertEqual(tuple(node.get_widths()), (1.0, 1.0, 1.0, 1.0))
                                match = re.search(r"colors:\s*rgba?\(([^)]+)\)", serialized)
                                self.assertIsNotNone(match)
                                assert match is not None
                                channels = [float(value) for value in match.group(1).split(",")]
                                colors.append(channels if len(channels) == 4 else channels + [1.0])
                        self.assertTrue(all(dim < bright for dim, bright in zip(colors[1][:3], colors[0][:3])))
                        self.assertEqual(colors[0][3], 1.0)
                        self.assertAlmostEqual(colors[1][3], 0.65)
                    finally:
                        window.destroy()
            finally:
                Gtk.StyleContext.remove_provider_for_display(display, provider)

    def test_window_controls_keep_native_hit_targets_and_palette_dots(self):
        try:
            gi = importlib.import_module("gi")
            gi.require_version("Gtk", "4.0")
            gi.require_version("Adw", "1")
            Gtk = importlib.import_module("gi.repository.Gtk")
            Adw = importlib.import_module("gi.repository.Adw")
            Gdk = importlib.import_module("gi.repository.Gdk")
        except (ImportError, ValueError):
            self.skipTest("GTK 4/libadwaita PyGObject is not available")
        if Gtk.get_minor_version() < 16 or not Gtk.init_check():
            self.skipTest("GTK 4.16+ and a display are required")
        Adw.init()
        settings = Gtk.Settings.get_default()
        self.addCleanup(settings.set_property, "gtk-enable-animations",
                        settings.get_property("gtk-enable-animations"))
        settings.set_property("gtk-enable-animations", False)
        display = Gdk.Display.get_default()
        native = Gtk.CssProvider()
        native.load_from_resource("/org/gnome/Adwaita/styles/gtk.css")
        Gtk.StyleContext.add_provider_for_display(
            display, native, Gtk.STYLE_PROVIDER_PRIORITY_USER + 1)
        self.addCleanup(Gtk.StyleContext.remove_provider_for_display, display, native)
        window = Gtk.Window()
        self.addCleanup(window.destroy)
        header = Gtk.HeaderBar(show_title_buttons=False)
        controls = Gtk.WindowControls(side=Gtk.PackType.END,
                                      decoration_layout=":minimize,maximize,close")
        header.pack_end(controls)
        window.set_titlebar(header)
        window.set_child(Gtk.Box())
        window.realize()
        window.allocate(500, 260, -1, None)
        buttons = {}
        child = controls.get_first_child()
        while child:
            for action in ("minimize", "maximize", "close"):
                if child.has_css_class(action):
                    buttons[action] = child
            child = child.get_next_sibling()
        self.assertEqual(set(buttons), {"minimize", "maximize", "close"})
        # Unmapped toplevels can report minimize/maximize as unavailable.
        for button in buttons.values():
            button.set_sensitive(True)
        native_sizes = {}
        for compact in (False, True):
            if compact:
                header.add_css_class("default-decoration")
            for action, button in buttons.items():
                for axis in (Gtk.Orientation.HORIZONTAL, Gtk.Orientation.VERTICAL):
                    native_sizes[compact, action, axis] = tuple(button.measure(axis, -1))[:2]
        header.remove_css_class("default-decoration")
        states = (Gtk.StateFlags.NORMAL, Gtk.StateFlags.PRELIGHT, Gtk.StateFlags.ACTIVE,
                  Gtk.StateFlags.FOCUSED | Gtk.StateFlags.FOCUS_VISIBLE,
                  Gtk.StateFlags.BACKDROP, Gtk.StateFlags.BACKDROP | Gtk.StateFlags.PRELIGHT,
                  Gtk.StateFlags.INSENSITIVE)
        clear_flags = Gtk.StateFlags.NORMAL
        for state in states:
            clear_flags |= state
        for stylesheet in ("gtk.css", "libadwaita.css"):
            css = (GTK / stylesheet).read_text(encoding="utf-8")
            backdrop = re.findall(r"--gp-window-control-bg: ([^;]+);", css)[-1]
            provider = Gtk.CssProvider()
            provider.load_from_path(str(GTK / stylesheet))
            Gtk.StyleContext.add_provider_for_display(
                display, provider, Gtk.STYLE_PROVIDER_PRIORITY_USER + 2)
            try:
                for compact in (False, True):
                    if compact:
                        header.add_css_class("default-decoration")
                    else:
                        header.remove_css_class("default-decoration")
                    for action, button in buttons.items():
                        image = button.get_child()
                        for axis in (Gtk.Orientation.HORIZONTAL, Gtk.Orientation.VERTICAL):
                            self.assertEqual(tuple(button.measure(axis, -1))[:2],
                                             native_sizes[compact, action, axis])
                        match = re.search(r"\." + action + r"\s*\{\s*--gp-window-control-bg: ([^;]+);", css)
                        self.assertIsNotNone(match)
                        for state in states:
                            with self.subTest(css=stylesheet, compact=compact, action=action, state=state):
                                button.unset_state_flags(clear_flags)
                                button.set_state_flags(state, False)
                                context = image.get_style_context()
                                shows_glyph = bool(state & (Gtk.StateFlags.PRELIGHT | Gtk.StateFlags.ACTIVE |
                                                            Gtk.StateFlags.FOCUS_VISIBLE))
                                self.assertEqual(context.get_color().alpha, float(shows_glyph))
                                snapshot = Gtk.Snapshot()
                                snapshot.render_background(context, 0, 0, 24, 24)
                                node = snapshot.to_node()
                                self.assertIsNotNone(node)
                                self.assertIn("radial-gradient", node.serialize().get_data().decode())
                                expected = Gdk.RGBA()
                                expected.parse(backdrop if state & Gtk.StateFlags.BACKDROP else match.group(1))
                                while hasattr(node, "get_child"):
                                    node = node.get_child()
                                actual = node.get_color_stops()[0].color
                                for channel in ("red", "green", "blue", "alpha"):
                                    self.assertAlmostEqual(getattr(actual, channel), getattr(expected, channel))
                        button.unset_state_flags(clear_flags)
                self.assertFalse(window.get_mapped())
            finally:
                header.remove_css_class("default-decoration")
                Gtk.StyleContext.remove_provider_for_display(display, provider)

    def test_gtk_css_parses(self):
        try:
            import gi
            gi.require_version("Gtk", "4.0")
            Gtk = importlib.import_module("gi.repository.Gtk")
        except (ImportError, ValueError):
            self.skipTest("GTK 4 PyGObject is not available")
        if (Gtk.get_major_version(), Gtk.get_minor_version()) < (4, 16):
            self.skipTest("CSS variables require GTK 4.16 or newer")
        for name in ("gtk.css", "gtk-dark.css", "libadwaita.css"):
            with self.subTest(stylesheet=name):
                errors = []
                provider = Gtk.CssProvider()
                provider.connect("parsing-error", lambda p, s, e, diagnostics=errors: diagnostics.append(str(e)))
                provider.load_from_path(str(GTK / name))
                self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
