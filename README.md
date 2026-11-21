# Viparu

Yaru-based **GTK 3, GTK 4 and GNOME Shell themes** combining light content,
dark headers, warm selections, blue controls and colored window dots.
Each variant has a fixed mixed light-content/dark-chrome appearance, unchanged
between GNOME Light and Dark modes.

| ID | Exact display and folder name | Sidebar |
| --- | --- | --- |
| `nile-blue` (default) | `Viparu-Nile-Blue` | Original petrol-blue appearance |
| `brown` | `Viparu-Brown` | Cocoa/rose-taupe brown with shared sidebar/Shell bronco hover |

`Viparu-Nile-Blue` preserves the original appearance unchanged. Brown uses an
80% `cocoa` / 20% `rose_taupe` sidebar base, then the existing 60% base / 40%
`almost_black` darkening. Sidebar/Shell hover shares the `bronco` role (mixed
85% with 15% sidebar background). Brown uses `tulip_tree` gold for sidebar
selection, Shell accents and active quick-toggle backgrounds; active toggle
text/icons use `chathams_blue`. Enabled toggles, checked or unchecked, use
`brownish_red` text/icons on hover and keyboard focus. Only unchecked toggles
receive a 70% `silver` / 30% `linen` hover/focus background; active toggles retain
their gold background.

Brown also swaps GTK content/card surfaces: content is `linen`, while cards use
the pale 60% `white` / 40% `linen` mix. Its general and control GTK accents use
`ocean`; dark headers and window-dot colors remain unchanged.

## Screenshots

### Nile Blue

![Viparu-Nile-Blue — original appearance](screenshot.png)

### Brown

![Viparu-Brown — cocoa/rose-taupe surfaces and ocean GTK accents](screenshot_brown.png)

## Release notes

- Two standalone themes: **Viparu-Nile-Blue** (original appearance unchanged)
  and **Viparu-Brown** (final cocoa/rose-taupe palette and gold Shell accents).
- Brown includes the swapped GTK surfaces, ocean GTK accents and distinct
  quick-toggle hover/keyboard-focus states described above.
- Both retain their fixed appearance for light and dark requests. Separate
  screenshots above show Nile Blue and Brown.
- Separate build folders and release archives preserve each variant's identity.
  Switching requires explicit theme selections and a GTK 4 installer update;
  original pre-Viparu backups are preserved.

## Quick start

1. Extract `Viparu-Nile-Blue.tar.gz` or `Viparu-Brown.tar.gz` into `~/.themes/`,
   keeping the exact folder name. For example,
   `~/.themes/Viparu-Nile-Blue/index.theme` must exist directly inside that folder.
2. **Enable the GNOME Shell component:** enable the **User Themes** extension
   and select **Viparu-Nile-Blue** or **Viparu-Brown** as the Shell theme in GNOME Tweaks.
3. **Select the legacy theme:** in **GNOME Tweaks → Appearance**, select the
   matching name for **Legacy Applications**. Labels may differ between GNOME versions.
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

**There is no single switch for all components.** First copy or extract the exact
standalone `Viparu-Nile-Blue/` or `Viparu-Brown/` folder into `~/.themes/`.
To switch variants, run `./install-gtk.sh --update` **from that destination folder**
for the libadwaita user layer, then select its matching **Legacy Applications**
and **Shell** themes separately in Tweaks.
The unchanged installer shares `viparu` ownership/backup state, retaining link/copy
mode and the original pre-Viparu backups. Existing users may keep their old
`Viparu/` directory while migrating to the new names; no settings change automatically.

## Building variants

`python3 -B scripts/build-theme.py` rebuilds only the local theme selected by the
plain `theme-variant` file (`nile-blue` by default).
`python3 -B scripts/build-theme.py --variants` instead builds both complete,
standalone source+compiled themes under `dist/themes/Viparu-Nile-Blue/` and
`dist/themes/Viparu-Brown/`, without rebuilding or modifying local root styles or
the desktop. Use `--variant brown` instead of `--variants` to build only Brown
in that same output directory. Copy the folders into `~/.themes/` keeping their exact names.

`python3 -B scripts/package-theme.py` packages both variants by default as
`dist/Viparu-Nile-Blue.tar.gz` and `dist/Viparu-Brown.tar.gz`. Packaging accepts
`--variant nile-blue` or `--variant brown` to package only one. Each extracted theme
includes its own `theme-variant`, so a default rebuild preserves its identity and colors.
See the development guide for shared palette and role sources.

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
