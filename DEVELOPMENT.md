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

The plain `theme-variant` file selects the local theme (`nile-blue` by default).
The default command rebuilds only that selection as before. An extracted variant's
own `theme-variant` preserves its identity and colors on a default rebuild.

The build generates the palette and variant assignments, prepares Shell sources, compiles all styles and
checks every image URL before publishing the compiled CSS and referenced assets.
GTK runtime URLs stay within each component's `assets/` directory. Only images
referenced by the compiled styles are copied from the vendored source artwork.

The build **does not install the theme, change desktop settings or run tests**.
In a linked GTK 4 installation its new outputs are visible through the existing
links, so restart applications to load them. Copy installations need an explicit
`./install-gtk.sh --update`.

## Standalone variant builds

```sh
python3 -B scripts/build-theme.py --variants
```

This builds **both** complete standalone source+compiled theme directories:

```text
dist/themes/Viparu-Nile-Blue/
dist/themes/Viparu-Brown/
```

It does not rebuild or modify local root styles or the desktop. Each directory
includes its own `theme-variant` and can be copied directly into `~/.themes/`.
Keep the exact display/folder names `Viparu-Nile-Blue` and `Viparu-Brown`.
To build only one standalone copy, use `--variant brown` or `--variant nile-blue`
instead of `--variants`. Neither option changes the local `theme-variant` selection.

## Palette and customization

- Edit shared `color-palette.json` for raw colors.
- `theme-variants.json` maps `nile-blue` and `brown` IDs to `name` and the
  `sidebar_base`/`sidebar_hover` palette variable names.
- The plain `theme-variant` file selects the root checkout's local variant.
- Edit shared `scss/_roles.scss` for semantic assignments, window-outline geometry
  and window-control colors.
- `color-palette.scss` and `scss/_variant.scss` are generated; do not edit them manually.
- `scss/_yaru-colors.scss` maps the shared roles onto Yaru's color API.

`Viparu-Nile-Blue` is the renamed original appearance. `Viparu-Brown` provisionally
uses `english_walnut` for the sidebar base and `rose_taupe` for hover; light linen,
header and control accents stay unchanged. Both variants look the same for light
and dark requests. The existing screenshot shows the original Nile Blue appearance,
not a Brown preview.

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
theme-variant             Plain local variant ID (nile-blue by default)
theme-variants.json        Variant names and sidebar palette-variable mappings
color-palette.json          Shared raw palette
scss/_variant.scss         Generated variant assignments; do not edit
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
| `scripts/build-theme.py` | Rebuild selected local theme; `--variants` builds both standalone themes, `--variant ID` builds one instead | Local generated palette/variant assignments, Shell staging, CSS and assets; with `--variants`, `dist/themes/Viparu-Nile-Blue/` and `dist/themes/Viparu-Brown/` without rebuilding/modifying root styles |
| `scripts/palette.py` | Generate SCSS from the JSON palette | `color-palette.scss`; `--check` is read-only |
| `gnome-shell/prepare_sources.py` | Transform the vendored Shell source copies | `gnome-shell/.build/scss/`; `--check` is read-only |
| `install-gtk.sh` | Explicit GTK 4 user installation and removal | Three config entries plus backup/ownership state; `--status` is read-only |
| `scripts/package-theme.py` | Build and package both variants by default; optional `--variant nile-blue` or `--variant brown` | Standalone variant outputs and corresponding `dist/Viparu-Nile-Blue.tar.gz` / `dist/Viparu-Brown.tar.gz` |

The vendored `scss/yaru/*/render-assets.sh` files are upstream artwork-maintenance
helpers, not project installation/build commands. Pre-rendered artwork is
included, so Inkscape and image optimizers are not needed for a normal build.

## Create release archives

From the project root:

```sh
python3 -B scripts/package-theme.py
```

This builds and packages both variants by default:

```text
dist/Viparu-Nile-Blue.tar.gz
dist/Viparu-Brown.tar.gz
```

To package only one, use either command:

```sh
python3 -B scripts/package-theme.py --variant nile-blue
python3 -B scripts/package-theme.py --variant brown
```

Each archive contains its exact top-level `Viparu-Nile-Blue/` or `Viparu-Brown/`
directory, matching its display name and `index.theme`, with compiled styles,
runtime artwork, corresponding sources, installer, documentation, developer checks
and license notices. Its own `theme-variant` ensures a default rebuild preserves
that variant's identity and colors. Keep the folder name when extracting into
`~/.themes/`; the source checkout itself may have any directory name.

No Git command is required; packaging also works from an extracted source package.
It includes current files, including uncommitted source edits, so review changes
before release. Standalone builds leave local root styles and desktop settings alone.

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
5. Upload the selected archives. Do not archive the entire development directory by hand.

The packaging command neither installs the theme nor runs test suites.

## Developer checks

Run the project and Shell regression checks separately:

```sh
python3 -B -m unittest discover -s tests -v
python3 -B -m unittest discover -s gnome-shell -p 'test_*.py' -v
```

GTK rendering checks require PyGObject, GTK 4.16+, libadwaita and a working display;
they are reported as skipped when those prerequisites are unavailable. No test
shows a window or writes desktop settings. Native libadwaita fixtures mask the
installed user CSS at process-local provider priority, and compare geometry with
and without `libadwaita.css` instead of pinning toolkit-specific padding values.
Traditional GTK checks use `gtk.css` separately. Color checks follow the exported
semantic roles, allowing the palette to change without restoring old colors.

The checks cover control states, header backgrounds and native layout, window
outlines/artwork, CSS parsing, assets, palette generation, packaging and installer
backup continuity. They are never invoked by builds or packaging. Passing these
checks does not replace manual application/Shell compatibility checks.
