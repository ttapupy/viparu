# Vintage-Pop-Art-Unified

A **Yaru-based GTK and GNOME Shell theme** with light content, dark headers,
petrol-blue sidebars, warm selections and colored window controls.

GTK widget shapes, layout and ordinary interaction states come from
[Yaru](https://github.com/ubuntu/yaru), not Ant-Bloody. Vintage adds its own palette,
color-role mapping, hybrid chrome and window-control artwork. See
[THIRD_PARTY.md](THIRD_PARTY.md) for authorship, source revisions and licenses.

## Components

| Component | Entry point | Foundation |
| --- | --- | --- |
| GTK 3.24 | `gtk-3.0/gtk.css` | Yaru GTK 3, including its libhandy adaptations |
| GTK 4 | `gtk-4.0/gtk.css` | Yaru GTK 4 for traditional theme loading |
| libadwaita user layer | `gtk-4.0/libadwaita.css` | Native libadwaita widget sizing with Vintage colors/artwork |
| GNOME Shell | `gnome-shell/gnome-shell.css` | Included GNOME Shell and Yaru sources |

Both GTK versions provide a `gtk-dark.css` identical to `gtk.css`. The single
hybrid appearance is intentional: it does not switch to an all-dark design when
an application requests a dark theme. Shell is always dark. There is no dedicated
high-contrast variant or bundled icon theme.

## Install and try the local theme

Keep the complete directory at:

```text
~/.themes/Vintage-Pop-Art-Unified/
```

1. In **GNOME Tweaks**, select **Vintage-Pop-Art-Unified** for legacy applications.
2. For GTK 4/libadwaita applications, explicitly run the installer below.
3. To use the Shell component, enable the **User Themes** extension and select
   **Vintage-Pop-Art-Unified** as the Shell theme separately.
4. Restart affected applications. A logout/login also restarts persistent processes.

### GTK 4 / libadwaita installation and updates

From the theme directory, run as your desktop user, **without sudo**:

```sh
./install-gtk.sh              # First install: symlinks; later runs: retain the mode
./install-gtk.sh --status     # Inspect the installation without changing it
```

The script manages exactly three entries under
`${XDG_CONFIG_HOME:-~/.config}/gtk-4.0/`: `gtk.css`, `gtk-dark.css` and `assets`.
Both CSS names point to **`gtk-4.0/libadwaita.css`**, not the full Yaru GTK widget
stylesheet; `assets` points to the GTK 4 asset folder. This avoids mixing Yaru's
complete widget layout with libadwaita's built-in layout. Rebuilding the theme
updates the linked contents without another copy;
applications may still need restarting. Do not move/delete the theme while its
links are active; rerun the installer from its new location if you move it.

For a self-contained copy instead of symlinks:

```sh
./install-gtk.sh --copy
./install-gtk.sh --update     # Refresh after rebuilding; retains copy mode
```

Use `--link` to switch back to symlinks. All image URLs stay within the GTK 4
`assets/` directory, including the window-control glyphs; no general
`~/.config/assets` directory or source SCSS files are installed.

Before the first installation, existing entries are backed up under
`${XDG_STATE_HOME:-~/.local/state}/vintage-pop-art-unified/gtk-4.0/previous/`.
Updates preserve that original backup. To remove the managed entries and restore
what was there before installation:

```sh
./install-gtk.sh --uninstall
```

Updates/uninstall refuse to overwrite CSS, links or assets changed by the user
or another tool. `settings.ini`, GTK 3 configuration, GSettings and Shell settings
are never changed. Evolve is not required.

**These are explicit, user-wide GTK 4 overrides. Changing the legacy theme in
GNOME Tweaks does not retarget or disable them.** Run `--uninstall` before a clean
comparison with another theme, or explicitly install the desired theme's files.

Nothing in the build runs this installer or activates the theme automatically.
The package is self-contained; the development machine's Yaru checkout is not needed.

### Application coverage

Modern libadwaita applications generally keep their built-in style when only the
legacy GTK theme is selected. The explicit installer loads Vintage at GTK's user
CSS priority so these applications can also use its appearance. This is a global
style override, not a supported libadwaita skin API: application-specific styles
and toolkit updates can require adjustments.

Flatpak applications may not see a symlink target outside their sandbox. Copy mode
avoids external asset paths, but sandbox permissions/theme visibility can still
need separate handling. The theme does not change GDM, icon selection,
window-button order or extension settings.

## Appearance and customization

- `color-palette.json`: raw colors.
- `color-palette.scss`: generated Sass variables; do not edit manually.
- `scss/_roles.scss`: shared semantic roles and geometry.
- `scss/_yaru-colors.scss`: maps the roles onto Yaru's GTK color API before widgets
  and drawing helpers are imported.

The established palette is retained: light linen-derived content, almost-black
headers, petrol sidebars, warm selections, blue controls, carmine focus rings and
`tulip_tree` window outlines. Minimize/maximize/close use `tulip_tree`, `cascade` and `carmine`; inactive
controls use `bronco`. Their 18px dots are CSS-painted, with recolorable SVG glyphs
on hover, press or keyboard focus. Native click-target geometry is retained.

**Header shrinking is disabled.** Traditional GTK applications retain Yaru's
header and control sizing; the libadwaita user layer retains libadwaita's sizing.
No custom header minimum height, control margins or global padding reset is
applied. Sidebar and content headers use the same native layout rules.
In toolbar views, the complete top-bar container paints the background outside
backdrop-faded window handles; header contents retain their native fading.

The user layer adds the single 1px `tulip_tree` window outline without importing
Yaru's additional window-decoration rules. Inactive outlines use an opaque darker
mix so the color stays uniform over both light content and dark sidebars.
Enabled switches use the independent
blue control role, including backdrop states; disabled styling remains native.
Suggested buttons have distinct darker hover/pressed colors. Some traditional
Yaru artwork, such as marked-scale handles, retains its original colors.

`$gp-folder-color` is reserved for future icon work; full-color folder icons are
still supplied by the selected icon theme.

## Build

Requirements: **Python 3.9+ and sassc / LibSass**. From the project root:

```sh
python3 -B scripts/build-theme.py
```

The build generates the palette, prepares Shell sources, compiles GTK 3, GTK 4
and Shell, and resolves all CSS image references before publishing the outputs.
Only referenced Yaru assets are copied to each GTK runtime `assets/` directory.
No Meson build, GResource compilation or installed Ant/Yaru theme is required.

A locally unpacked compiler under `.build-tools/usr/` is used if no system
`sassc` is available. `.build-tools/`, including private backups and source staging,
is ignored development data and must not be included in a published package.
End users loading the compiled styles do not need a compiler.

### Source layout

```text
scss/yaru/                  Vendored Yaru GTK foundation and source artwork
scss/gtk-3.0.scss            GTK 3 entry point
scss/gtk-4.0.scss            Traditional GTK 4 theme entry point
scss/libadwaita-4.0.scss     Color/artwork-only user layer for libadwaita
scss/_yaru-colors.scss       Shared Yaru color mapping
scss/_gtk3-chrome.scss       GTK 3 hybrid chrome and window controls
scss/_gtk4-chrome.scss       GTK 4 named colors, hybrid chrome and window outline

scss/_controls.scss          Color-only control adaptations
scss/_window-controls.scss   GTK 4 window-control artwork
assets/window-*.svg          Source glyphs, copied into both GTK runtime asset folders
install-gtk.sh              Explicit GTK 4 link/copy installer, status and removal
gnome-shell/                GNOME/Yaru Shell sources and build entry point
common/                     Shared contrast and color utilities
licenses/                   Third-party license texts and authors
```

GTK sources are pinned to Yaru revision
`7f18973e05607c609c4b972f0dd9bff36fa2a13e`. Details are in
[the vendored source notes](scss/yaru/README.md). The Shell component retains its
existing GNOME/Yaru source snapshot; see [its build notes](gnome-shell/README.md).

## Validation status

The Yaru rebase is ready for a local visual comparison, not a claim of identical
appearance across every GNOME application. GTK 4 uses modern CSS features; older
GTK/libadwaita releases need separate verification. Shell sources target GNOME
Shell 51 selectors, so other Shell versions also require verification.

Regression checks under `tests/` are developer tools, not part of installation or
normal builds. The previous Ant-specific appearance expectations have not all
been reviewed against the new Yaru baseline. No automatic test suite is invoked
by the build.

## Credits

- **Yaru contributors and Canonical** — current GTK foundation, Shell adaptations
  and artwork; upstream authors are included in `licenses/yaru/AUTHORS`.
- **GNOME / Adwaita / GTK contributors** — foundations inherited through Yaru and
  the included Shell sources.
- **EliverLara / Ant-Bloody**, itself based on **evopop-gtk-theme** — the previous
  GTK foundation and an ongoing visual reference. The Ant widget source trees and
  old bitmap assets are no longer part of the active theme; the earlier state is
  preserved in Git history.
- **Marco Trevisan / Canonical** and **Björn Ottosson** — contrast/Oklab utilities.

Source-specific licenses and notices remain applicable. See
[`LICENSE`](LICENSE), [`THIRD_PARTY.md`](THIRD_PARTY.md) and `licenses/`.
