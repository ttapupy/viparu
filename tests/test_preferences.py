"""Compare the installed user layer with native libadwaita, never showing windows."""

import itertools
import unittest

from gtk_test_support import GtkTestCase, SCHEMES


class PreferencesTests(GtkTestCase):
    def combo_group(self, content):
        group = self.Adw.PreferencesGroup()
        content.append(group)
        first = self.Adw.ActionRow(title="First", activatable=True)
        row = self.Adw.ComboRow(
            title="New icon placement", subtitle="Where to put the next icon",
            model=self.Gtk.StringList.new(["Top left", "Bottom right"]), selected=1)
        last = self.Adw.ActionRow(title="Last", activatable=True)
        for item in (first, row, last):
            group.add(item)
        return first, row, last

    def test_combo_inline_geometry_states_and_corners_stay_native(self):
        Gtk = self.Gtk
        for scheme in SCHEMES:
            native = {}
            for stylesheet in (None, "libadwaita.css"):
                with self.subTest(css=stylesheet, scheme=scheme), \
                        self.themed_window(stylesheet, scheme) as (window, content):
                    first, row, last = self.combo_group(content)
                    window.allocate(640, 260, -1, None)
                    inline = next(w for w in self.descendants(row)
                                  if isinstance(w, Gtk.ListView) and w.has_css_class("inline"))
                    item = inline.get_first_child()
                    value = next(w for w in self.descendants(inline) if isinstance(w, Gtk.Label))
                    title = next(w for w in self.descendants(row)
                                 if isinstance(w, Gtk.Label) and w.has_css_class("title"))
                    subtitle = next(w for w in self.descendants(row)
                                    if isinstance(w, Gtk.Label) and w.has_css_class("subtitle"))
                    self.assertEqual(value.get_text(), "Bottom right")
                    self.assertFalse(value.get_selectable())
                    self.assertFalse(item.get_state_flags() & Gtk.StateFlags.SELECTED)
                    states = self.states() + (("disabled", Gtk.StateFlags.INSENSITIVE),)
                    for state_name, state in states:
                        with self.subTest(state=state_name):
                            for widget in (first, row, last):
                                self.set_state(window, widget, state)
                            record = (
                                tuple(self.geometry(w) for w in (row, inline, item, title, subtitle)),
                                self.background(inline)[3], self.background(item)[3],
                                self.pixels(self.paint(first))[0][3],
                                self.pixels(self.paint(last))[-1][3],
                                self.paint(row, "focus") is not None,
                                subtitle.get_opacity(),
                            )
                            if stylesheet is None:
                                native[state_name] = record
                            else:
                                self.assertEqual(record, native[state_name])
                                self.assertEqual(self.foreground(title), self.role_color(content, "view-fg-color"))
                                # Native subtitles dim through opacity, not a separate text color.
                                self.assertEqual(self.foreground(subtitle), self.foreground(title))
                    row.add_css_class("has-open-popup")
                    self.set_state(window, row, Gtk.StateFlags.PRELIGHT | Gtk.StateFlags.FOCUS_VISIBLE)
                    popup_record = self.geometry(row), self.background(inline)[3], self.paint(row, "focus") is not None
                    if stylesheet is None:
                        native["popup"] = popup_record
                    else:
                        self.assertEqual(popup_record, native["popup"])

    def test_dropdown_combo_and_suffix_menu_keep_native_geometry(self):
        Gtk = self.Gtk
        for scheme, kind in itertools.product(SCHEMES, ("dropdown", "combobox", "menubutton")):
            native = {}
            for stylesheet in (None, "libadwaita.css"):
                with self.subTest(css=stylesheet, scheme=scheme, control=kind), \
                        self.themed_window(stylesheet, scheme) as (window, content):
                    group = self.Adw.PreferencesGroup()
                    content.append(group)
                    row = self.Adw.ActionRow(title="Placement")
                    group.add(row)
                    if kind == "dropdown":
                        control = Gtk.DropDown.new_from_strings(["Bottom right", "Top left"])
                    elif kind == "combobox":
                        control = Gtk.ComboBoxText()
                        control.append_text("Bottom right")
                        control.set_active(0)
                    else:
                        control = Gtk.MenuButton(label="Bottom right")
                        control.set_popover(Gtk.Popover(child=Gtk.Label(label="Choices")))
                    control.set_valign(Gtk.Align.CENTER)
                    row.add_suffix(control)
                    window.allocate(640, 140, -1, None)
                    button = next(w for w in self.descendants(control) if isinstance(w, Gtk.Button))
                    states = self.states() + (("checked", Gtk.StateFlags.CHECKED),)
                    for state_name, state in states:
                        with self.subTest(state=state_name):
                            self.set_state(window, button, state)
                            record = (self.geometry(control), self.geometry(button),
                                      self.paint(button, "frame") is not None,
                                      self.paint(button, "focus") is not None,
                                      self.background(button)[3] > 0)
                            if stylesheet is None:
                                native[state_name] = record
                            else:
                                self.assertEqual(record, native[state_name])

    def test_combo_popup_keeps_native_selection_feedback_without_opening(self):
        Gtk = self.Gtk
        for scheme in SCHEMES:
            native = {}
            for stylesheet in (None, "libadwaita.css"):
                with self.subTest(css=stylesheet, scheme=scheme), \
                        self.themed_window(stylesheet, scheme) as (window, content):
                    _, row, _ = self.combo_group(content)
                    window.allocate(640, 260, -1, None)
                    popover = next(w for w in self.descendants(row) if isinstance(w, Gtk.Popover))
                    listing = next(w for w in self.descendants(popover) if isinstance(w, Gtk.ListView))
                    item = listing.get_first_child()
                    self.assertIsNotNone(item)
                    for state_name, state in self.states():
                        with self.subTest(state=state_name):
                            self.set_state(window, item, state)
                            item.set_state_flags(Gtk.StateFlags.SELECTED, False)
                            color = self.background(item)
                            record = (self.geometry(item), color[3] > 0, self.paint(item, "focus") is not None)
                            if stylesheet is None:
                                native[state_name] = record
                            else:
                                self.assertEqual(record, native[state_name])
                            # Native combo popups may use a checkmark rather than an opaque selected row.
                            self.assertTrue(item.get_state_flags() & Gtk.StateFlags.SELECTED)
                    self.assertFalse(popover.get_visible())
                    self.assertFalse(popover.get_mapped())

    def test_ordinary_file_listview_stays_opaque(self):
        for scheme in SCHEMES:
            with self.subTest(scheme=scheme), \
                    self.themed_window("libadwaita.css", scheme) as (window, content):
                listing = self.Gtk.ListView()
                content.append(listing)
                window.allocate(640, 200, -1, None)
                for state in (self.Gtk.StateFlags.NORMAL, self.Gtk.StateFlags.BACKDROP):
                    self.set_state(window, listing, state)
                    self.assertEqual(self.background(listing), self.role_color(content, "view-bg-color"))

    def test_direct_and_wrapped_headers_keep_native_geometry_and_outer_background(self):
        Gtk = self.Gtk
        for scheme in SCHEMES:
            native = None
            for stylesheet in (None, "libadwaita.css"):
                with self.subTest(css=stylesheet, scheme=scheme), \
                        self.themed_window(stylesheet, scheme) as (window, content):
                    panes = Gtk.Box()
                    content.append(panes)
                    bars = []
                    for sidebar in (True, False):
                        pane = Gtk.Box(css_classes=["sidebar-pane"] if sidebar else [])
                        view = self.Adw.ToolbarView()
                        header = self.Adw.HeaderBar(title_widget=Gtk.Label(label="Files"))
                        header.set_show_start_title_buttons(False)
                        header.set_show_end_title_buttons(False)
                        view.add_top_bar(header if sidebar else self.Adw.Bin(child=header))
                        view.set_content(Gtk.Box(vexpand=True))
                        pane.append(view)
                        panes.append(pane)
                        top = next(w for w in self.descendants(view) if w.has_css_class("top-bar"))
                        bars.append((header, top, sidebar))
                    window.allocate(900, 500, -1, None)
                    geometry = tuple(self.geometry(header) for header, _, _ in bars)
                    if stylesheet is None:
                        native = geometry
                    else:
                        self.assertEqual(geometry, native)
                        for state in (Gtk.StateFlags.NORMAL, Gtk.StateFlags.BACKDROP):
                            for header, top, sidebar in bars:
                                self.set_state(window, header, state)
                                role = "sidebar-bg-color" if sidebar else "headerbar-bg-color"
                                self.assertEqual(self.background(top), self.role_color(content, role))
                                self.assertEqual(self.background(header)[3], 0)


if __name__ == "__main__":
    unittest.main()
