# Viparu development and release guide

## Build requirements

- Python **3.9 or newer**; project tooling uses only the standard library.
- **sassc / LibSass**. On Ubuntu/Debian, the compiler package is `sassc`.

A system `sassc` is preferred. For local development only, the build also accepts
an unpacked compiler under `.build-tools/usr/bin/sassc` and its local LibSass
libraries. This private directory is not shipped and is not required by users.
No external upstream checkout, Meson build, GResource compilation or network
access is needed.

From the project root:

```sh
python3 -B scripts/build-theme.py
```

The build generates the palette, prepares Shell sources, compiles all styles and
checks every image URL before publishing the compiled CSS and referenced assets.
GTK runtime URLs stay within each component's `assets/` directory. Only images
referenced by the compiled styles are copied from the vendored source artwork.

The build **does not install the theme, change desktop settings or run tests**.
In a linked GTK 4 installation its new outputs are visible through the existing
links, so restart applications to load them. Copy installations need an explicit
`./install-gtk.sh --update`.

## Palette and customization

- Edit `color-palette.json` for raw colors.
- Edit `scss/_roles.scss` for semantic assignments, window-outline geometry and
  window-control colors.
- `color-palette.scss` is generated; do not edit it manually.
- `scss/_yaru-colors.scss` maps the shared roles onto Yaru's color API.

The 18px window dots use `tulip_tree` for minimize, `cascade` for maximize,
`carmine` for close and `bronco` when inactive. Their source glyphs live in
`assets/window-*-symbolic.svg`. The build copies them into the GTK runtime asset
folders. Native hit targets and header sizing are retained.

The GTK 4 user layer paints toolbar backgrounds outside backdrop-faded handles.
Its single 1px outline becomes an opaque darker mix when inactive, keeping the
same edge color over light and dark surfaces. Switches and grouped choices use
blue control roles independently of warm selection colors. Some vendored artwork
retains its upstream colors.

`$gp-folder-color` is reserved for future artwork; it does not recolor the icon
theme. Fully dark and high-contrast variants are not currently provided.

## Source layout

```text
color-palette.json          Raw palette
scss/_roles.scss           Shared semantic roles
scss/_yaru-colors.scss     Yaru color mapping
scss/_gtk3-chrome.scss     GTK 3 chrome and window controls
scss/_gtk4-chrome.scss     GTK 4 chrome, named colors and outline
scss/_controls.scss        Color-only control adaptations
scss/_window-controls.scss GTK 4 window-control artwork
scss/gtk-3.0.scss           GTK 3 entry point
scss/gtk-4.0.scss           Traditional GTK 4 entry point
scss/libadwaita-4.0.scss    Minimal GTK 4/libadwaita user layer
scss/yaru/                 Vendored GTK sources and source artwork
gnome-shell/               Shell sources, preparation script and compiled CSS
common/                    Shared contrast and color utilities
licenses/                  Upstream license texts and authors
```

GTK sources are pinned to Yaru revision
`7f18973e05607c609c4b972f0dd9bff36fa2a13e`. See
[the vendored source notes](scss/yaru/README.md),
[Shell build notes](gnome-shell/README.md) and
[third-party provenance](THIRD_PARTY.md).

Do not replace native header dimensions or import the full GTK 4 widget theme
into the libadwaita user layer. The separate entry points are intentional.

## Script responsibilities

| Script | Purpose | Writes |
| --- | --- | --- |
| `scripts/build-theme.py` | Complete local build | Generated palette, Shell staging, compiled CSS and referenced assets |
| `scripts/palette.py` | Generate SCSS from the JSON palette | `color-palette.scss`; `--check` is read-only |
| `gnome-shell/prepare_sources.py` | Transform the vendored Shell source copies | `gnome-shell/.build/scss/`; `--check` is read-only |
| `install-gtk.sh` | Explicit GTK 4 user installation and removal | Three config entries plus backup/ownership state; `--status` is read-only |
| `scripts/package-theme.py` | Rebuild and create a clean distribution archive | Build outputs and `dist/Viparu.tar.gz` |

The vendored `scss/yaru/*/render-assets.sh` files are upstream artwork-maintenance
helpers, not project installation/build commands. Pre-rendered artwork is
included, so Inkscape and image optimizers are not needed for a normal build.

## Create a release archive

From the project root:

```sh
python3 -B scripts/package-theme.py
```

This rebuilds first, then creates:

```text
dist/Viparu.tar.gz
```

The archive contains one top-level `Viparu/` directory with
compiled styles, runtime artwork, corresponding source files, installer,
documentation, developer checks and license notices. No Git command is required;
the same script works from an extracted source package. It packages the current
files, including uncommitted source edits, so review your changes before release.
The source checkout may have any directory name; the archive and its top-level
folder are always named **Viparu**, matching `index.theme`. Install the extracted
`Viparu/` folder to make the theme discoverable by that name.

An explicit list of project paths excludes `.git/`, `.build-tools/`, `dist/`,
Shell `.build/` staging and Python caches. Local config backups and diagnostic
screenshots must never be distributed. Symlinks inside package inputs are
rejected rather than silently embedding external files. The previous archive is
replaced only after the new archive has been written successfully.

Before publishing:

1. Review `git diff` and the compatibility claims in the README.
2. Confirm the supplied styles match the intended sources by using the packaging
   command above.
3. Review the archive contents and keep all corresponding sources, credits and
   license notices together.
4. Check the appearance manually on the toolkit/Shell versions you intend to
   support. Record those versions in release notes; do not claim unverified
   compatibility.
5. Upload the archive. Do not archive the entire development directory by hand.

The packaging command neither installs the theme nor runs test suites.

## Developer checks

`tests/` and `gnome-shell/test_prepare_sources.py` contain developer regression
checks, not installation requirements. They are never invoked by builds or
packaging. Their presence is not a claim that all expectations have been audited
for the current theme or that every supported application has been tested.
