# Viparu

A Yaru-based **GTK 3, GTK 4 and GNOME Shell theme** combining light linen content,
dark headers and petrol-blue sidebars with warm orange selections, blue controls
and colored window dots.
It has the same output when you set Light or Dark mode in Gnome. This is intentional.

The theme keeps native header and control sizing. A thin yellow window outline
becomes darker, without transparency, when the window is inactive.

## Quick start

1. Extract the release archive into `~/.themes/`, keeping its **Viparu** folder.
   `~/.themes/Viparu/index.theme` must exist directly inside that folder.
2. **Theming GNOME Shell:** enable the **User Themes**
   extension and select **Viparu** as the Shell theme in GNOME Tweaks.
3. **Theming Legacy apps: **In **GNOME Tweaks → Appearance**, select **Viparu** for **Legacy Applications**.
   Labels may differ between GNOME versions.
4. **Theming native  GTK 4/libadwaita apps (Nautilus, Settings, etc.):** To style these applications too, open a terminal in the theme
   directory and run **as your desktop user, without sudo**:

   ```sh
   ./install-gtk.sh
   ```

5. Fully restart affected applications, or log out and back in.

Compiled styles and artwork are included. **No build, separately installed Yaru
theme or compiler is needed to use the theme.** The GTK 4 installer requires Bash
and standard GNU/Linux file utilities; it does not download anything.

**The GTK 4 installation is a user-wide override. Switching the legacy theme in
Tweaks does not disable it.** To restore the previous GTK 4 files, run
`./install-gtk.sh --uninstall` before removing the theme directory.

## Documentation

- **[Usage guide](USAGE.md)** — installation, updates, backups, removal, Flatpak
  limitations and troubleshooting.
- **[Development and release guide](DEVELOPMENT.md)** — palette customization,
  builds, script responsibilities and clean distribution archives.
- **[Third-party credits and licenses](THIRD_PARTY.md)** — source provenance and
  upstream notices.

## Components

| Component | Stylesheet | Foundation |
| --- | --- | --- |
| GTK 3.24 | `gtk-3.0/gtk.css` | Yaru, including libhandy adaptations |
| Traditional GTK 4 | `gtk-4.0/gtk.css` | Yaru |
| GTK 4/libadwaita user layer | `gtk-4.0/libadwaita.css` | Native libadwaita layout with Viparu colors and artwork |
| GNOME Shell | `gnome-shell/gnome-shell.css` | Included GNOME Shell and Yaru sources |

The installer uses the **libadwaita user layer**, not the complete Yaru widget
stylesheet, so native application layout is preserved. Both GTK versions have a
`gtk-dark.css` identical to `gtk.css`: the mixed light-content/dark-chrome
appearance is intentional, including when an application requests dark mode.
Shell is always dark.

## Compatibility and scope

- GTK 3 targets GTK 3.24. GTK 4 uses modern CSS features; older GTK/libadwaita
  versions are not guaranteed to work.
- The included Shell sources target **GNOME Shell 51**. Other Shell versions and
  extensions may need adjustments; universal compatibility is not claimed.
- Libadwaita styling is an explicit GTK user-CSS override, not a supported
  libadwaita theme API. Application-specific CSS and toolkit updates may affect it.
- Flatpak applications may need additional sandbox/theme configuration. See the
  [usage guide](USAGE.md#flatpak-applications).
- No icon theme, high-contrast variant or GDM login-screen theme is included.
  Window-button order and desktop settings are not changed by the scripts.

## Credits and licensing

GTK widget layout, drawing helpers and ordinary interaction states come from
[Yaru](https://github.com/ubuntu/yaru), built on GNOME's Adwaita/GTK work. Viparu
adds its palette, semantic color mapping, chrome and window-control artwork.

Thanks to **Yaru contributors and Canonical**, **GNOME/Adwaita/GTK contributors**,
**Marco Trevisan** and **Björn Ottosson** for the included foundations and color
utilities.

The project's root license is [GPL-3.0](LICENSE). Included third-party code and
artwork retain their own licenses, including LGPL and CC BY-SA terms. See
[THIRD_PARTY.md](THIRD_PARTY.md) and `licenses/`; keep these notices when
redistributing the theme.
