"""Control colors for both GTK entry points; native libadwaita layout stays intact."""

import colorsys
import itertools
import unittest

from gtk_test_support import GtkTestCase, SCHEMES, STYLESHEETS


def shade(color, delta):
    hue, lightness, saturation = colorsys.rgb_to_hls(*(c / 255 for c in color[:3]))
    return tuple(round(c * 255) for c in colorsys.hls_to_rgb(
        hue, min(1, max(0, lightness + delta)), saturation)) + (color[3],)


class ControlsTests(GtkTestCase):
    def test_sidebar_labels_and_selection(self):
        Gtk = self.Gtk
        for stylesheet, scheme, kind in itertools.product(
                STYLESHEETS, SCHEMES, ("sidebar", "navigation-sidebar", "stacksidebar")):
            with self.subTest(css=stylesheet, scheme=scheme, sidebar=kind), \
                    self.themed_window(stylesheet, scheme) as (window, content):
                if kind == "stacksidebar":
                    stack = Gtk.Stack()
                    stack.add_titled(Gtk.Box(), "appearance", "Appearance")
                    stack.add_titled(Gtk.Box(), "keyboard", "Keyboard & Mouse")
                    sidebar = Gtk.StackSidebar(stack=stack)
                    content.append(sidebar)
                    content.append(stack)
                    row, other = [widget for widget in self.descendants(sidebar)
                                  if isinstance(widget, Gtk.ListBoxRow)]
                    label = row.get_child()
                else:
                    sidebar = Gtk.ListBox(css_classes=[kind])
                    label = Gtk.Label(label="Keyboard & Mouse")
                    row = Gtk.ListBoxRow(child=label)
                    other = Gtk.ListBoxRow(child=Gtk.Label(label="Appearance"))
                    sidebar.append(row)
                    sidebar.append(other)
                    content.append(sidebar)
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
                            role = "gp-selection-fg" if selected else "sidebar-fg-color"
                            self.assertEqual(self.foreground(label), self.role_color(content, role))
                            if selected:
                                if (stylesheet == "gtk.css" and kind == "stacksidebar"
                                        and state & Gtk.StateFlags.PRELIGHT and not state & Gtk.StateFlags.BACKDROP):
                                    # Yaru's :selected:hover:dir() rule outranks the generic override.
                                    expected = shade(self.role_color(content, "gp-control-hover-bg"), -0.05)
                                    self.assert_color_close(self.background(row), expected)
                                else:
                                    role = "gp-selection-hover-bg" if state & Gtk.StateFlags.PRELIGHT else "gp-selection-bg"
                                    self.assertEqual(self.background(row), self.role_color(content, role))

    def test_checked_linked_toggle_uses_independent_blue_control_roles(self):
        Gtk = self.Gtk
        for stylesheet, scheme in itertools.product(STYLESHEETS, SCHEMES):
            with self.subTest(css=stylesheet, scheme=scheme), \
                    self.themed_window(stylesheet, scheme) as (window, content):
                listing = Gtk.ListBox(css_classes=["boxed-list"])
                linked = Gtk.Box(css_classes=["linked"])
                button = Gtk.ToggleButton(label="Left", active=True)
                linked.append(button)
                linked.append(Gtk.ToggleButton(label="Right"))
                listing.append(Gtk.ListBoxRow(child=linked))
                content.append(listing)
                for state_name, state in self.states():
                    with self.subTest(state=state_name):
                        self.set_state(window, button, state)
                        self.assertTrue(button.get_active())
                        self.assertEqual(self.foreground(button.get_child()),
                                         self.role_color(content, "gp-control-accent-fg"))
                        role = "gp-control-accent-hover-bg" if state & Gtk.StateFlags.PRELIGHT else "gp-control-accent-bg"
                        self.assertEqual(self.background(button), self.role_color(content, role))

    def test_linked_toggle_geometry_stays_native_and_stable_when_checked(self):
        Gtk = self.Gtk
        for scheme in SCHEMES:
            native = None
            for stylesheet in (None,) + STYLESHEETS:
                with self.subTest(css=stylesheet, scheme=scheme), \
                        self.themed_window(stylesheet, scheme) as (window, content):
                    linked = Gtk.Box(css_classes=["linked"])
                    button = Gtk.ToggleButton(label="Left start button")
                    linked.append(button)
                    linked.append(Gtk.ToggleButton(label="Right start button"))
                    content.append(linked)
                    measurements = {}
                    for state_name, state in self.states():
                        for checked in (False, True):
                            button.set_active(checked)
                            self.set_state(window, button, state)
                            linked.allocate(500, 60, -1, None)
                            first_ok, first = button.compute_bounds(linked)
                            last_ok, last = linked.get_last_child().compute_bounds(linked)
                            self.assertTrue(first_ok and last_ok)
                            gap = last.get_x() - first.get_x() - first.get_width()
                            measurements[state_name, checked] = self.geometry(button), gap
                        self.assertEqual(measurements[state_name, False], measurements[state_name, True])
                    if stylesheet is None:
                        native = measurements
                    elif stylesheet == "libadwaita.css":
                        self.assertEqual(measurements, native)

    def test_switch_trough_and_thumb_follow_control_roles(self):
        Gtk = self.Gtk
        for stylesheet, scheme in itertools.product(STYLESHEETS, SCHEMES):
            with self.subTest(css=stylesheet, scheme=scheme), \
                    self.themed_window(stylesheet, scheme) as (window, content):
                switch = Gtk.Switch()
                content.append(switch)
                slider = next(widget for widget in self.descendants(switch)
                              if widget.get_css_name() == "slider")
                accent = self.role_color(content, "gp-control-accent-bg")
                for checked in (False, True):
                    switch.set_active(checked)
                    switch.set_state(checked)
                    for state_name, state in self.states():
                        with self.subTest(checked=checked, state=state_name):
                            self.set_state(window, switch, state)
                            self.set_state(window, slider, state)
                            trough = self.background(switch)
                            if checked:
                                self.assertEqual(trough, accent)
                                thumb = self.background(slider)
                                self.assertEqual(thumb[3], 255)
                                self.assertGreater(min(thumb[:3]), max(trough[:3]),
                                                   "The thumb must contrast with the blue trough")
                            else:
                                self.assertGreater(trough[3], 0)
                                self.assertNotEqual(trough, accent)
                                self.assertLessEqual(max(trough[:3]) - min(trough[:3]), 40)

    def test_check_and_radio_use_toolkit_colors_and_render_their_glyphs(self):
        Gtk = self.Gtk
        for stylesheet, scheme, kind in itertools.product(STYLESHEETS, SCHEMES, ("check", "radio")):
            with self.subTest(css=stylesheet, scheme=scheme, indicator=kind), \
                    self.themed_window(stylesheet, scheme) as (window, content):
                button = Gtk.CheckButton()
                content.append(button)
                if kind == "radio":
                    peer = Gtk.CheckButton()
                    content.append(peer)
                    button.set_group(peer)
                button.set_active(True)
                indicator = button.get_first_child()
                self.assertEqual(indicator.get_css_name(), kind)
                button.allocate(48, 32, -1, None)
                role = "gp-selection-bg" if stylesheet == "gtk.css" else "accent-bg-color"
                base = self.role_color(content, role)
                for state_name, state in self.states():
                    with self.subTest(state=state_name):
                        self.set_state(window, button, state)
                        self.set_state(window, indicator, state)
                        fill = self.background(indicator)
                        ink = self.foreground(indicator)
                        self.assertNotEqual(fill[:3], ink[:3])
                        if stylesheet == "gtk.css":
                            # Yaru uses HSL +/-7% for pressed/hovered checked indicators.
                            delta = -0.07 if state & Gtk.StateFlags.ACTIVE else 0.07 if state & Gtk.StateFlags.PRELIGHT else 0
                            self.assert_color_close(fill, shade(base, delta))
                            self.assertEqual(ink, self.role_color(content, "gp-selection-fg"))
                        elif not state & (Gtk.StateFlags.PRELIGHT | Gtk.StateFlags.ACTIVE):
                            self.assert_color_close(fill, base)
                            self.assertEqual(ink, self.role_color(content, "accent-fg-color"))
                        width, height = indicator.get_width(), indicator.get_height()
                        self.assertGreater(min(width, height), 0)
                        snapshot = Gtk.Snapshot()
                        snapshot.render_background(indicator.get_style_context(), 0, 0, width, height)
                        snapshot.render_frame(indicator.get_style_context(), 0, 0, width, height)
                        type(indicator).do_snapshot(indicator, snapshot)
                        node = snapshot.to_node()
                        self.assertIsNotNone(node)
                        pixels = self.pixels(node, width, height)
                        # Small SVG glyphs may have no completely un-antialiased pixel.
                        self.assertTrue(any(max(abs(p[c] - ink[c]) for c in range(4)) <= 6 for p in pixels),
                                        f"The {kind} glyph must paint its foreground color")


if __name__ == "__main__":
    unittest.main()
