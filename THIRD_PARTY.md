# Third-party source provenance

Vintage-Pop-Art-Unified is a derivative theme. Local palette changes, source
reorganization and new controls do not remove the authorship or license
requirements of the original foundations. No separately installed Ant-Bloody or
Yaru theme is needed at runtime, but their included source contributions remain
substantial.

## GTK foundation: Ant-Bloody / Ant

- **Author/project maintainer:** [EliverLara](https://github.com/EliverLara).
- **Direct starting point:** [Ant-Bloody](https://github.com/EliverLara/Ant-Bloody),
  the Bloody variant of [Ant](https://github.com/EliverLara/Ant).
- **Earlier foundation:** [evopop-gtk-theme](https://github.com/solus-project/evopop-gtk-theme),
  explicitly credited by Ant-Bloody's README.
- **License:** GPL-3.0; the inherited license text is retained in
  [`LICENSE`](LICENSE). Preserve any additional notices in individual sources.

### Included and adapted code

The Ant-Bloody GTK 3.20 foundation now lives under `scss/gtk-3.0/`; its GTK 4
foundation lives under `scss/gtk-4.0/`. Both include adapted drawing helpers,
common state/focus declarations and GNOME application styles. Their `_widgets.scss`
files list the active widget partials: currently 34 for GTK 3 and 33 for GTK 4.

The inherited code covers ordinary widgets, chrome, lists, menus/popovers,
containers, dialogs, indicators and window-decoration foundations. It is not
accurate to describe Ant-Bloody as merely an inspiration for the color scheme.

### Project-specific additions and adaptations

- A shared JSON palette and semantic role assignments replace the original colors.
- The public GTK named-color API and palette-based GTK 3 adaptation are local.
- Switches, checkboxes and radio buttons use palette-painted CSS instead of the
  original fixed-color bitmap control assets.
- Window controls use palette-painted dots and local recolorable SVG glyphs;
  their old bitmap rules have been removed from the active source foundation.
- Toolbar flattening no longer applies to GTK 4 suggested/destructive actions.
- Suggested action buttons have distinct hover and pressed colors.
- Modern libadwaita color, chrome, preferences and window-outline adapters are local.
- Build scripts and Shell palette preprocessing are local project tooling.

These descriptions distinguish new/adapted work from inherited code; they do not
claim that every retained upstream widget rule has been rewritten.

## GNOME Shell foundation

- **Project:** GNOME Shell and its contributors.
- **Location:** `gnome-shell/upstream/theme/gnome-shell-sass/`.
- **License text:** [`COPYING`](gnome-shell/upstream/theme/gnome-shell-sass/COPYING)
  and notices in the included sources.

The Shell drawing, common styles and widget sources are prepared into generated
copies for palette substitution. The vendored inputs retain their provenance.

## Yaru Shell adaptations and artwork

- **Project:** [Yaru](https://github.com/ubuntu/yaru), Canonical and Yaru contributors.
- **Locations:** `gnome-shell/src/gnome-shell-sass/` and the referenced
  `gnome-shell/src/*.svg` artwork.
- **License text:** [`COPYING`](gnome-shell/src/gnome-shell-sass/COPYING) and
  source/artwork-specific notices.

The active Shell build uses the Yaru dock/tweaks layers and local artwork; it does
not require the original Yaru Meson build or a separately installed Yaru theme.
Keep embedded artwork metadata and source copyright notices when redistributing.

## Contrast and color utilities

- `common/sass-utils.scss`: copyright Canonical Ltd; its header credits
  Marco Trevisan and specifies LGPL-2.1-or-later. The full license text is
  included in [`licenses/LGPL-2.1`](licenses/LGPL-2.1).
- `common/oklab.scss`: based on the Oklab color space by **Björn Ottosson**;
  its header identifies the original code as public domain with an alternative
  MIT license. See the original reference and license links retained there.

Author names and their diacritics are preserved; translating project documentation
must not alter attribution or remove original copyright/license notices.
