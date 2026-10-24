# Vintage-Pop-Art-Unified

A coordinated GTK and GNOME Shell theme with **light application content, dark
headers, petrol-blue sidebars, warm selections and colored window controls**.

**GTK foundation:** substantially adapted from
[Ant-Bloody](https://github.com/EliverLara/Ant-Bloody) by
[EliverLara](https://github.com/EliverLara), itself based on
[evopop-gtk-theme](https://github.com/solus-project/evopop-gtk-theme).
This is a derivative theme, not a clean-room implementation or merely a palette
inspired by Ant-Bloody. See [Credits and source provenance](#credits-and-source-provenance)
and [THIRD_PARTY.md](THIRD_PARTY.md).

## Components

One theme directory contains independently selectable components:

| Component | Loadable stylesheet | Purpose |
| --- | --- | --- |
| GTK 3 | `gtk-3.0/gtk.css` | GTK 3.24 applications, using the shared palette |
| GTK 4 | `gtk-4.0/gtk.css` | Complete GTK 4 widget theme and libadwaita overrides |
| libadwaita layer | `gtk-4.0/libadwaita.css` | Optional color/control overrides without the complete widget theme |
| GNOME Shell | `gnome-shell/gnome-shell.css` | Panel, overview, quick settings, notifications and other Shell surfaces |

The package does not include an icon theme. Full-color folder icons are controlled
by the selected icon theme; symbolic icons generally inherit their UI foreground.

### One intentional hybrid appearance

There is **no separate all-light or all-dark design**. Both GTK versions provide a
`gtk-dark.css` identical to their `gtk.css`, so an application requesting a dark
variant still receives the same hybrid appearance. GNOME Shell is always dark.

Separate light/dark variants are not required for a GTK or Shell theme. This
choice intentionally does not follow automatic light/dark switching. A dedicated
high-contrast variant is not provided.

## Installation and activation

Place the complete `Vintage-Pop-Art-Unified` directory in `~/.themes/` or another
theme directory supported by your desktop. Do not copy just the CSS: its relative
asset paths must remain intact.

- **GTK 3:** select `Vintage-Pop-Art-Unified` as the legacy application theme in
  GNOME Tweaks or your desktop's theme manager.
- **GNOME Shell:** enable the User Themes extension and select
  `Vintage-Pop-Art-Unified` as the Shell theme. GTK and Shell selections are separate.
- **GTK 4/libadwaita:** selecting a legacy GTK theme does not reliably theme
  libadwaita applications. Apply the GTK 4 stylesheet with a compatible tool such
  as Evolve, or explicitly load the optional `libadwaita.css` override layer.

Libadwaita does **not** provide a supported general-purpose third-party skin API.
These overrides can need adjustments after GTK, libadwaita or application updates.
Back up existing `~/.config/gtk-4.0/gtk.css` before changing user overrides.
Application-specific styles and Flatpak sandbox access may require separate handling.

This project does not change the GDM login-screen theme, icon theme, window-button
order or extension settings. Building it does not activate it or modify GSettings.

## Palette and customization

- [`color-palette.json`](color-palette.json): raw color values.
- [`color-palette.scss`](color-palette.scss): generated Sass variables; do not edit by hand.
- [`scss/_roles.scss`](scss/_roles.scss): shared semantic colors and geometry.

Important roles include:

| Role | Setting |
| --- | --- |
| Light content surfaces | `$gp-view-bg`, `$gp-window-bg`, `$gp-card-bg` |
| Dark header and sidebar | `$gp-header-bg`, `$gp-sidebar-bg`, `$gp-chrome-fg`, `$gp-sidebar-fg` |
| Warm selections and focus | `$gp-selection-bg`, `$gp-selection-fg`, `$gp-focus-ring` |
| Suggested action buttons | `$gp-accent-bg`, `$gp-accent-fg`, `$gp-suggested-hover-bg`, `$gp-suggested-active-bg` |
| Blue controls | `$gp-control-accent-bg`, `$gp-control-accent-fg`, `$gp-control-accent-hover-bg` |
| Window outline | `$gp-window-border-color`, `$gp-window-border-backdrop-color`, `$gp-window-border-width`, `$gp-window-border-radius` |
| Minimize / maximize / close | `$gp-window-minimize-bg`, `$gp-window-maximize-bg`, `$gp-window-close-bg` |
| Inactive window controls | `$gp-window-control-backdrop-bg` |
| Shell surfaces and accents | `$gp-shell-*` roles |

Window controls use CSS-painted dots and recolorable SVG glyphs, rather than
Ant-Bloody's fixed-color PNGs. The GTK 4 dots are 18 logical pixels across while
retaining libadwaita-sized click targets. Glyphs appear on hover, press or keyboard
focus. Suggested action buttons darken distinctly on hover and press.

`$gp-folder-color` is a reserved color role; it is not connected to icon-theme assets.

## Building

Requirements: **Python 3 and sassc / LibSass**. No Ant-Bloody installation, external
Sass include path, Meson build or GResource compilation is required.

From the project root:

```sh
python3 -B scripts/build-theme.py
```

The build regenerates the palette, prepares the Shell sources, compiles all four
entry points, and publishes the resulting stylesheets only after compilation
succeeds. The fixed hybrid `gtk-dark.css` files are generated at the same time.

On Ubuntu, `sassc` can be installed with `sudo apt install sassc`. This development
checkout can also use the locally unpacked compiler under `.build-tools/usr/` if
no system compiler is available. `.build-tools/` is machine-specific development
equipment, not a runtime theme dependency.

The sources still use some legacy compound `@extend` expressions supported by
LibSass; Sass emits deprecation warnings for these. Dart Sass is not currently a
drop-in replacement. End users loading the generated CSS do not need a compiler.

### Active source layout

```text
scss/
  _roles.scss                 Shared palette assignments
  _gtk-colors.scss            Shared GTK widget color API
  _gtk-public-colors.scss     Named colors exported to GTK applications
  gtk-3.0.scss                GTK 3 entry point
  gtk-3.0/                   Adapted GTK 3 foundation and own overrides
  gtk-4.0.scss                GTK 4 entry point
  gtk-4.0/                   Adapted GTK 4 foundation
  _libadwaita.scss            Modern colors, chrome and window outline
  _controls.scss             Palette-painted GTK 4 controls
  _preferences.scss          Modern libadwaita preferences adapters
  _window-controls.scss      Colored GTK 4 window controls
  libadwaita-4.0.scss         Optional libadwaita-only entry point
gnome-shell/                 Shell entry point, sources, artwork and preparation
common/                      Shell color and contrast utilities
scripts/                     Palette generation and build tools
```

Source consolidation is in progress. The entry points above are authoritative;
remaining legacy files outside their import graphs are not required by the build.
See [the Shell build notes](gnome-shell/README.md) for its preprocessing details.

## Compatibility and validation

- GTK 3 targets GTK 3.24. The palette-based GTK 3 adaptation compiles but still
  needs its own visual review before a public release.
- The GTK 4 custom-property layer targets GTK 4.16+ and libadwaita 1.6+; identical
  behavior on older releases is not guaranteed.
- The vendored Shell sources target GNOME Shell 51 selectors. Other Shell versions
  require verification; User Themes compatibility is not guaranteed across releases.
- A successful Sass build is not a guarantee of appearance in every application.
  Application overrides, extensions and sandbox restrictions can affect the result.

Optional developer checks, run explicitly rather than as part of every build:

```sh
python3 -B scripts/palette.py --check
python3 -B -m unittest discover -s tests -v
python3 -B -m unittest discover -s gnome-shell -p 'test_*.py' -v
```

## Credits and source provenance

### Ant-Bloody — EliverLara

The GTK foundation is a **substantial derivative of Ant-Bloody by EliverLara**,
not just its mixed light/dark idea. The current build imports **33 GTK 4 widget
partials and 34 GTK 3 widget partials** adapted from that foundation, as well as
its drawing helpers, common state/focus setup and GNOME application rules.

Inherited areas include:

- Base widget states, ordinary buttons, text entries, spin buttons and links.
- Header bars, toolbars, action bars, sidebars, lists and tree views.
- Menus, popovers, dialogs, notifications, infobars and tooltips.
- Tabs/notebooks, panes, frames, expanders and path bars.
- Scrollbars, scales, progress/level bars, spinners, calendars and color choosers.
- Window-decoration foundations and, for GTK 3, file-chooser rules.

The shared palette and semantic roles, CSS-painted switches/checks/radios,
colored window controls and their SVG glyphs, stronger suggested-button states,
modern libadwaita preferences adapters, window-outline overrides and build tooling
were added or adapted for this project. These additions do not erase the
provenance of the underlying GTK foundation.

Ant-Bloody credits [evopop-gtk-theme](https://github.com/solus-project/evopop-gtk-theme)
as its own foundation. Its GPL-3.0 license is retained in [`LICENSE`](LICENSE).

### GNOME Shell, Yaru and color utilities

The Shell theme is based on the included **GNOME Shell and Yaru sources**, not
Ant-Bloody's Shell styling. Credit belongs to their respective GNOME and Yaru
contributors, including Canonical. Their existing notices and license files remain
with the sources.

The Oklab conversion utilities credit **Björn Ottosson**; the contrast utilities
retain their Canonical/Marco Trevisan notices. See
[`THIRD_PARTY.md`](THIRD_PARTY.md) for source locations and license references.
