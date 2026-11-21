# Viparu usage guide

## 1. Install the theme directory

Extract `Viparu-Nile-Blue.tar.gz` or `Viparu-Brown.tar.gz` into `~/.themes/`,
keeping the exact display/folder name `Viparu-Nile-Blue` or `Viparu-Brown`.
For example:

```text
~/.themes/Viparu-Nile-Blue/
├── theme-variant
├── index.theme
├── install-gtk.sh
├── gtk-3.0/
├── gtk-4.0/
└── gnome-shell/
```

Keep the remaining source, documentation and license files as well. Compiled CSS
and artwork are supplied; building is only necessary after changing the sources.
Alternatively, `python3 -B scripts/build-theme.py --variants` creates both complete
standalone source+compiled directories in `dist/themes/`; copy them into `~/.themes/`
without renaming them. This does not rebuild or modify local root styles or the desktop.

`Viparu-Nile-Blue` preserves the original appearance unchanged. See the
[README screenshots](README.md#screenshots) for both variants: `screenshot.png`
shows Nile Blue and `screenshot_brown.png` shows Brown. Each variant retains its
own fixed mixed light/dark appearance for both light and dark requests.

`Viparu-Brown` uses an 80% `cocoa` / 20% `rose_taupe` sidebar base, then the
existing 60% base / 40% `almost_black` darkening. Its shared sidebar/Shell hover
uses 85% `bronco` / 15% sidebar background. Sidebar selection, Shell accents and
active quick-toggle backgrounds use `tulip_tree`; active toggle text/icons use
`chathams_blue`. Enabled checked and unchecked toggles use `brownish_red`
text/icons on hover and keyboard focus. Only unchecked toggles get a 70%
`silver` / 30% `linen` hover/focus background; active toggles retain gold.
GTK content is `linen`, cards use the pale 60% `white` / 40% `linen` mix, and
both general and control GTK accents use `ocean`. Dark headers and window-dot
colors remain unchanged.

Run all installation commands as your desktop user, **not with sudo**. They do
not require administrator access or a network connection.

## 2. Enable the GNOME Shell component (optional)

Install and enable the **User Themes** GNOME Shell extension using your
distribution's extension tools. Then select **Viparu-Nile-Blue** or **Viparu-Brown**
as the Shell theme in GNOME Tweaks.

The included sources target GNOME Shell 51. Other versions and dock extensions
can use different selectors or override parts of the theme. The installer does
not install extensions, select a Shell theme or replace GDM's login-screen theme.

## 3. Select the GTK theme

In **GNOME Tweaks → Appearance → Legacy Applications**, select
**Viparu-Nile-Blue** or **Viparu-Brown**, matching your Shell selection.
The setting's name can vary with the desktop version.
This selects the ordinary GTK theme, including GTK 3 and GTK 4 applications that
honor the theme setting.

Modern libadwaita applications generally retain their built-in appearance when
only this setting is changed. Use the separate step below to style them too.

## 4. Enable the GTK 4/libadwaita user layer

Open a terminal in the chosen directory, for example `~/.themes/Viparu-Nile-Blue/`,
and run:

```sh
./install-gtk.sh
./install-gtk.sh --status
```

The first command installs symlinks by default. Later runs preserve the existing
link/copy mode. The status command is read-only.

### What is installed

The installer manages exactly these entries under the GTK 4 user configuration
folder, normally `~/.config/gtk-4.0/`:

| Entry | Source |
| --- | --- |
| `gtk.css` | `gtk-4.0/libadwaita.css` |
| `gtk-dark.css` | `gtk-4.0/libadwaita.css` |
| `assets` | `gtk-4.0/assets/` |

Both CSS names intentionally use the small libadwaita layer. **Do not substitute
`gtk-4.0/gtk.css` there**: it contains the full Yaru widget stylesheet, whose
layout rules can conflict with libadwaita's built-in widgets.

`XDG_CONFIG_HOME` and `XDG_STATE_HOME` are honored when set to absolute paths.
The script does not change `settings.ini`, GTK 3 configuration, GSettings, Shell
settings, window-button order or icon selection.

### Link mode versus copy mode

- **Link mode** follows changes in the theme directory. Keep that directory in
  place while the installation is active.
- **Copy mode** creates independent CSS and asset copies in the GTK 4 configuration
  folder. Refresh them after updating or rebuilding the theme.

```sh
./install-gtk.sh --copy      # Install copies, or switch from links to copies
./install-gtk.sh --link      # Install links, or switch back to links
./install-gtk.sh --update    # Refresh while retaining the current mode
./install-gtk.sh --help
```

If the theme directory is moved while links are active, run `--update` from its
new location to retarget the managed links.

### Backups and safety

Before the first installation, existing CSS files, links and assets are backed
up under:

```text
~/.local/state/viparu/gtk-4.0/previous/
```

With a custom `XDG_STATE_HOME`, the same relative path is used below that directory.
Updates preserve the original backup. Do not delete the installer's state folder:
it records ownership of the installed entries and the files needed for restoration.
Existing installations may retain their original state location; `--status` shows
the actual backup path. No manual state-directory renaming is necessary.

Updates and removal refuse to overwrite entries modified by another tool or by
hand. If this happens, preserve those changes separately and restore the managed
entries before trying again; do not delete the backups to bypass the check.

**These overrides affect GTK 4 applications for this user regardless of the
legacy theme selected in Tweaks.** Uninstall the override before comparing an
unrelated GTK theme.


## 5. Reload applications

Fully quit and reopen affected applications. Closing a window is not always
sufficient: applications such as Files/Nautilus can keep a background process
running. A logout/login is a reliable way to restart the entire session.

There is no need to rebuild just to enable the supplied theme. Header and
control sizing stays native. The fixed mixed light/dark design is used for both
light and dark requests; a separate fully dark variant is not provided.

## Updating

1. Keep the theme in the same directory and replace it with the new release, or
   update the checkout. Rebuild only if working with changed source files.
2. Run `./install-gtk.sh --update`. This refreshes copies and preserves link mode.
   When using links, rebuilt file contents are already visible through them.
3. Fully restart affected applications. A session restart may be needed for Shell.

Do not discard the installer's state or original backups during an update.

## Switching variants or migrating from Viparu

**There is no single switch for all components.** Copy the built standalone
folder or extract its release archive into `~/.themes/`, keeping the exact
`Viparu-Nile-Blue/` or `Viparu-Brown/` folder name. Select the destination's
**Legacy Applications** and **Shell** themes separately in Tweaks (Shell needs
User Themes). For the libadwaita user layer, explicitly run the installer from
**inside that destination directory** (for example `~/.themes/Viparu-Brown/`):

```sh
./install-gtk.sh --update
```

The unchanged `install-gtk.sh` uses shared `viparu` ownership/backup state across
both variants and the old theme. This retargets links or refreshes copies while
retaining the current link/copy mode and original pre-Viparu backups; do not
uninstall first or rename the state directory. Select the matching **Legacy
Applications** and **Shell** themes separately in Tweaks, then restart applications.

Existing `Viparu` users can keep their original directory while migrating and
select the new names. No desktop settings are changed automatically.

Each extracted archive contains its own plain `theme-variant` file.
`python3 -B scripts/build-theme.py` rebuilds that selected local theme, preserving
its identity and colors (`nile-blue` is the checkout default). The `--variants`
and `--variant ID` options build standalone copies instead of switching this local
selection; see [the development guide](DEVELOPMENT.md) for builds and packaging.

## Removing or switching to an unrelated theme

From the theme directory, run:

```sh
./install-gtk.sh --uninstall
```

This removes the managed GTK 4 entries and restores whatever existed before the
first installation. If no previous entries existed, the managed entries are
simply removed. Existing prior overrides, if any, become active again.

Next, select another legacy application theme and, if used, another Shell theme
in Tweaks. Restart applications. You can then remove the Viparu theme directory.

Uninstall does not reset desktop settings or remove unrelated files.

## Flatpak applications

A sandbox may not be able to follow links into the host's theme directory. Copy
mode avoids that external symlink target:

```sh
./install-gtk.sh --copy
```

This alone does **not** guarantee Flatpak coverage: the application must also be
able to see the GTK configuration, and its runtime or bundled styles may differ.
Use your distribution's per-application sandbox tools if additional access is
needed. This project does not grant filesystem permissions or install Flatpak
runtime theme extensions automatically.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Theme is missing from Tweaks | Check the directory name and ensure `index.theme` is not nested inside a second project folder. |
| GTK 3 changed but libadwaita did not | Run the explicit GTK 4 installer, inspect `--status`, then fully restart the application. |
| Switching the legacy theme leaves GTK 4 styled | Run `--uninstall`; the user override is independent of the legacy setting. |
| Changes are missing in copy mode | Run `--update` after replacing or rebuilding the theme. |
| Managed links have missing targets | Restore the theme directory or run `--update` from its new location. |
| Update/removal reports modified entries | Preserve your edits and resolve the changed entries; do not remove the original backups. |
| A single application looks different | Its own CSS, sandbox or toolkit version may override the theme. |
| Shell remains unchanged | Check the User Themes extension, the separately selected Shell theme and GNOME Shell version. |

When reporting an issue, include your distribution, GTK/libadwaita or GNOME Shell
version, application name, installation mode, `./install-gtk.sh --status` output
and a screenshot. Check the output for private paths before sharing it.
