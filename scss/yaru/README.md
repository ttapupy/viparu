# Vendored Yaru GTK foundation

Source: https://github.com/ubuntu/yaru

Snapshot: `7f18973e05607c609c4b972f0dd9bff36fa2a13e` (`Upload to stonking`).

The GTK 3 and GTK 4 source directories originate from `gtk/src/default/gtk-3.0`
and `gtk/src/default/gtk-4.0` in that revision. Copyright notices are retained.
License texts and upstream authors are provided under `licenses/yaru/` at the
project root. Upstream Yaru is based on GNOME's Adwaita/GTK styles.

Vintage entry points import the color definitions, apply `_yaru-colors.scss`,
then import Yaru's drawing, widget and tweak layers. Project-specific chrome,
header sizing and window-control artwork are applied last. There is no external
source path or runtime dependency on an installed Yaru theme.

The included rendered assets and their SVG sources belong to the same snapshot.
The build copies only images actually referenced by the generated GTK CSS into
the corresponding `gtk-3.0/assets/` and `gtk-4.0/assets/` runtime directories.
Some embedded artwork retains upstream colors; the main UI colors come from
Vintage's semantic roles.
