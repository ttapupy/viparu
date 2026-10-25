# Viparu — GNOME Shell component

`gnome-shell.scss` builds the standalone `gnome-shell.css` loaded by the User
Themes extension. This component is based on the included GNOME Shell and Yaru
sources. See [source credits](../THIRD_PARTY.md) and the
[user installation guide](../USAGE.md#2-enable-the-gnome-shell-component-optional).

## Building

The recommended command from the project root is:

```sh
python3 -B scripts/build-theme.py
```

For a Shell-only rebuild after generating the shared palette:

```sh
python3 -B gnome-shell/prepare_sources.py
sassc -t expanded gnome-shell/gnome-shell.scss gnome-shell/gnome-shell.css
```

Compile the entry point in its original location: all imports are relative and
no external include path, upstream Meson build or GResource compilation is needed.
The stylesheet references artwork relative to `gnome-shell.css`; keep the
referenced `src/*.svg` files when installing the theme.

## Source layers

1. `../scss/_roles.scss`: shared palette assignments and Shell roles.
2. `_gp-colors.scss`: maps the upstream/Yaru color-variable API to those roles
   before widgets derive their colors.
3. Prepared upstream drawing, common styles and widget partials.
4. Prepared Yaru dock and tweaks: geometry, typography, panel, lock screen,
   popovers and contrast adjustments.
5. `_gp-tweaks.scss`: a palette-based CSS focus cue replacing missing Metro artwork.

`common/sass-utils.scss` and its `oklab.scss` dependency supply the contrast guard.
The guard is intentional: an accent/surface combination that cannot meet the
required contrast causes a build error rather than silently producing unreadable UI.

## Source preparation

`prepare_sources.py` reads the vendored `src/` and `upstream/` inputs without
modifying them. It writes generated copies only under `.build/scss/`. That
directory can be regenerated and is not a runtime theme dependency.

The preparation step:

- Replaces direct `-st-accent-color` and `-st-accent-fg-color` expressions with
  the theme's Shell-specific roles.
- Maps known literal neutral/RGBA colors to the shared palette while preserving
  comments, strings and selectors.
- Preserves the exact transparent `rgba(3,2,1,0)` occlusion sentinel used upstream.
- Converts known `resource:///org/gnome/shell/theme/...` artwork URLs into local
  `src/*.svg` paths relative to the generated CSS.
- Replaces two unavailable Metro artwork URLs with `none`; the local tweaks
  supply their focus feedback without those images.
- Rejects unknown artwork, literal RGBA colors and incomplete source imports.

The optional `--check` flag verifies prepared sources without writing them.

## Compatibility and limitations

- A single `dark` / `normal` variant is intentional; no light or high-contrast
  Shell variant is provided.
- The vendored source snapshot uses GNOME Shell 51 selectors and runtime color
  functions. Other Shell versions need verification.
- SVG artwork retains its own embedded colors unless explicitly recolored.
- Lock-screen rules belong to the Shell stylesheet, but this project does not
  install or replace the system GDM login-screen theme.
- Dock extensions and application-specific inline styles can override theme rules.

Optional developer checks are separate from normal builds:

```sh
python3 -B -m unittest discover -s gnome-shell -p 'test_*.py' -v
```
