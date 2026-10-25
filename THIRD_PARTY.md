# Third-party source provenance

Viparu is a derivative theme. Recoloring, source reorganization
and project-specific controls do not remove upstream authorship or license
requirements. The package includes the sources and artwork it needs; no
separately installed upstream theme is required.

## Current GTK foundation: Yaru

- Project: https://github.com/ubuntu/yaru
- Authors: Yaru contributors and Canonical; the upstream authors list is retained
  in [`licenses/yaru/AUTHORS`](licenses/yaru/AUTHORS).
- Source revision: `7f18973e05607c609c4b972f0dd9bff36fa2a13e`
  (`Upload to stonking`).
- Source locations in that revision: `gtk/src/default/gtk-3.0/` and
  `gtk/src/default/gtk-4.0/`.
- Local locations: `scss/yaru/gtk-3.0/` and `scss/yaru/gtk-4.0/`.
- License texts: `licenses/yaru/COPYING`, `COPYING.LGPL-2.1`,
  `COPYING.LGPL-3.0`, and `LICENSE_CCBYSA`, together with notices in the files.

The included GTK sources provide the actual drawing helpers, widget layout,
interaction states, GTK 3 application rules and libhandy adaptations. Yaru itself
builds on GNOME's Adwaita/GTK foundation. Keep the original copyright notices.
Yaru uses mixed licensing; do not assume the project's root GPL license replaces
source-specific or artwork-specific terms.

Yaru SVG/PNG artwork is distributed under its Creative Commons
Attribution-ShareAlike 4.0 terms. Runtime image copies under `gtk-3.0/assets/` and
`gtk-4.0/assets/` come from this source snapshot. SVG source artwork and original
metadata are retained in the vendored source directories.

## Project-specific layers

The shared JSON palette and semantic roles, `_yaru-colors.scss` mapping, hybrid
chrome, stronger suggested-button state colors,
colored window-control dots, local SVG glyphs and build tooling are project work.
These layers are imported around the Yaru foundation. The build does not install
user CSS or modify desktop settings. The separate, explicitly invoked `install-gtk.sh` links or
copies the targeted `gtk-4.0/libadwaita.css` user layer and artwork into the user's
GTK 4 configuration, with backups and uninstall support; it does not install the
full Yaru widget stylesheet there or change GSettings. Header/control sizing is
left to Yaru for traditional GTK themes and to libadwaita for the user layer.


## GNOME Shell and Yaru Shell layers

The Shell component includes these GNOME Shell and Yaru source layers:

- `gnome-shell/upstream/theme/gnome-shell-sass/`: GNOME Shell sources and their
  [`COPYING`](gnome-shell/upstream/theme/gnome-shell-sass/COPYING).
- `gnome-shell/src/gnome-shell-sass/`: Yaru dock/tweaks and their
  [`COPYING`](gnome-shell/src/gnome-shell-sass/COPYING).
- Referenced `gnome-shell/src/*.svg`: Yaru artwork with retained embedded metadata.

Shell palette preprocessing writes generated copies without modifying those
vendored inputs. The GTK and Shell snapshots are maintained separately; they are
not claimed to originate from the same upstream revision.

## Contrast and color utilities

- `common/sass-utils.scss`: copyright Canonical Ltd; its header credits
  Marco Trevisan and specifies LGPL-2.1-or-later. Full text:
  [`licenses/LGPL-2.1`](licenses/LGPL-2.1).
- `common/oklab.scss`: based on Oklab by **Björn Ottosson**. Its header identifies
  the original code as public domain with an alternative MIT license and retains
  the original reference/license URLs.

Original copyright notices, author names and their diacritics must be preserved.
