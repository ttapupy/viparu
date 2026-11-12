"""Release naming and isolated installer-state regressions; no desktop changes."""

import configparser
import importlib.util
import json
import os
import shutil
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("package_theme", ROOT / "scripts/package-theme.py")
assert SPEC is not None and SPEC.loader is not None
package = importlib.util.module_from_spec(SPEC)
with patch.object(sys, "path", [str(ROOT / "scripts"), *sys.path]):
    SPEC.loader.exec_module(package)
    from theme_variants import copy_project, generate_variant, load_variants, selected_variant


class ReleaseTests(unittest.TestCase):
    def test_theme_identity_matches_release_name(self):
        metadata = configparser.ConfigParser()
        metadata.read(ROOT / "index.theme")
        key, variant = selected_variant(ROOT)
        self.assertIn(key, load_variants(ROOT))
        self.assertEqual(metadata["Desktop Entry"]["Name"], variant["name"])
        self.assertEqual(metadata["X-GNOME-Metatheme"]["GtkTheme"], variant["name"])

    def test_shell_is_the_second_installation_step(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        usage = (ROOT / "USAGE.md").read_text(encoding="utf-8")
        self.assertIn("2. **Enable the GNOME Shell component", readme)
        self.assertIn("## 2. Enable the GNOME Shell component", usage)
        self.assertLess(usage.index("## 2."), usage.index("## 3."))

    def test_public_documentation_uses_current_name(self):
        for name in ("README.md", "USAGE.md", "DEVELOPMENT.md", "THIRD_PARTY.md",
                     "gnome-shell/README.md", "scss/yaru/README.md"):
            with self.subTest(document=name):
                text = (ROOT / name).read_text(encoding="utf-8")
                self.assertNotIn("vintage", text.lower())

    def test_archives_are_variant_named_in_arbitrary_checkout(self):
        for selection in (None, "brown"):
            with self.subTest(selection=selection), tempfile.TemporaryDirectory(
                    prefix="unrelated-checkout-") as directory:
                root = Path(directory)
                for name in package.FILES:
                    (root / name).write_text("fixture\n", encoding="utf-8")
                for name in package.DIRECTORIES:
                    (root / name).mkdir()
                    (root / name / "included.txt").write_text("source\n", encoding="utf-8")
                for name in ("theme-variants.json", "color-palette.json", "theme-variant"):
                    shutil.copy2(ROOT / name, root / name)
                generate_variant(root)
                # Even a non-executable checkout must ship an executable installer.
                (root / "install-gtk.sh").chmod(0o600)
                variants = load_variants(root)
                keys = [selection] if selection else list(variants)

                def mock_build(*args, **kwargs):
                    for key in keys:
                        theme = root / "dist/themes" / variants[key]["name"]
                        copy_project(theme, key, root)
                        generate_variant(theme)
                        for private in (".git", ".build-tools", "dist", "gnome-shell/.build",
                                        "scripts/__pycache__", "scss/.private"):
                            path = theme / private
                            path.mkdir(parents=True, exist_ok=True)
                            (path / "private.txt").write_text("private", encoding="utf-8")
                        (theme / "scripts/stale.pyc").write_bytes(b"private")
                        (theme / "scripts/stale.pyo").write_bytes(b"private")

                arguments = ["--variant", selection] if selection else ["--variants"]
                argv = ["package-theme.py", "--variant", selection] if selection else ["package-theme.py"]
                with patch.object(package, "ROOT", root), \
                        patch.object(package.subprocess, "run", side_effect=mock_build) as build, \
                        patch.object(sys, "argv", argv):
                    self.assertEqual(package.main(), 0)
                    build.assert_called_once_with(
                        [sys.executable, "-B", str(root / "scripts/build-theme.py"), *arguments],
                        cwd=root, check=True, timeout=600,
                    )
                self.assertEqual({p.name for p in (root / "dist").glob("*.tar.gz")},
                                 {variants[key]["name"] + ".tar.gz" for key in keys})
                for key in keys:
                    name = variants[key]["name"]
                    with tarfile.open(root / "dist" / f"{name}.tar.gz") as archive:
                        members = archive.getmembers()
                        expected = {f"{name}/{path}" for path in package.FILES}
                        expected.update(f"{name}/{path}/included.txt" for path in package.DIRECTORIES)
                        expected.add(f"{name}/scss/_variant.scss")
                        self.assertEqual({member.name for member in members}, expected)
                        self.assertTrue(all(member.isfile() for member in members))
                        self.assertEqual(archive.getmember(f"{name}/install-gtk.sh").mode, 0o755)
                        self.assertTrue(all(member.uid == member.gid == 0 for member in members))
                        self.assertTrue(all(member.uname == member.gname == "" for member in members))
                        self.assertEqual(archive.extractfile(f"{name}/theme-variant").read(),
                                         (key + "\n").encode())
                        metadata = configparser.ConfigParser()
                        metadata.read_string(archive.extractfile(f"{name}/index.theme").read().decode())
                        self.assertEqual(metadata["Desktop Entry"]["Name"], name)
                        self.assertEqual(metadata["X-GNOME-Metatheme"]["GtkTheme"], name)

    def test_unknown_package_variant_does_not_build(self):
        with patch.object(package.subprocess, "run") as build, \
                patch.object(sys, "argv", ["package-theme.py", "--variant", "unknown"]):
            self.assertEqual(package.main(), 1)
            build.assert_not_called()


@unittest.skipIf(os.geteuid() == 0, "The user installer must not run as root")
class InstallerStateTests(unittest.TestCase):
    def test_switch_variants_preserves_mode_and_original_overrides(self):
        for initial_mode in ("link", "copy"):
            with self.subTest(mode=initial_mode), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                config = root / "config/gtk-4.0"
                config.mkdir(parents=True)
                originals = {"gtk.css": "original light\n", "gtk-dark.css": "original dark\n",
                             "assets/original.svg": "original asset\n"}
                for name, content in originals.items():
                    path = config / name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(content, encoding="utf-8")
                (config / "settings.ini").write_text("[Settings]\n", encoding="utf-8")
                themes = {}
                for key, variant in load_variants(ROOT).items():
                    theme = root / variant["name"]
                    assets = theme / "gtk-4.0/assets"
                    assets.mkdir(parents=True)
                    shutil.copy2(ROOT / "install-gtk.sh", theme / "install-gtk.sh")
                    (theme / "gtk-4.0/libadwaita.css").write_text(f"/* {key} */\n", encoding="utf-8")
                    (assets / "variant.svg").write_text(key, encoding="utf-8")
                    themes[key] = theme
                environment = os.environ.copy()
                environment.update(HOME=str(root), XDG_CONFIG_HOME=str(root / "config"),
                                   XDG_STATE_HOME=str(root / "state"))
                state = root / "state/viparu/gtk-4.0"

                def run(key, action, success=True):
                    result = subprocess.run(
                        ["bash", str(themes[key] / "install-gtk.sh"), action],
                        env=environment, capture_output=True, text=True, timeout=10,
                    )
                    if success:
                        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    else:
                        self.assertNotEqual(result.returncode, 0)
                        self.assertIn("Changed or replaced", result.stderr)
                    return result.stdout

                other_mode = "copy" if initial_mode == "link" else "link"
                steps = (("nile-blue", "--" + initial_mode, initial_mode),
                         ("brown", "--update", initial_mode),
                         ("nile-blue", "--" + other_mode, other_mode),
                         ("brown", "--update", other_mode))
                for key, action, mode in steps:
                    run(key, action)
                    self.assertEqual((state / "mode").read_text().strip(), mode)
                    self.assertEqual((state / "theme-dir").read_text().strip(), str(themes[key]))
                    status = run("nile-blue", "--status")
                    self.assertIn(f"Mode: {mode}\n", status)
                    self.assertIn(f"Theme: {themes[key]}\n", status)
                    self.assertIn(f"Original backups: {state}/previous", status)
                    for name, content in originals.items():
                        self.assertEqual((state / "previous" / name).read_text(), content)
                    for name in ("gtk.css", "gtk-dark.css", "assets"):
                        path = config / name
                        source = themes[key] / "gtk-4.0" / (
                            "assets" if name == "assets" else "libadwaita.css")
                        self.assertEqual(path.is_symlink(), mode == "link")
                        if mode == "link":
                            self.assertEqual(path.readlink(), source)
                        elif name != "assets":
                            self.assertEqual(path.read_bytes(), source.read_bytes())
                    self.assertEqual((config / "assets/variant.svg").read_text(), key)
                    self.assertEqual((config / "settings.ini").read_text(), "[Settings]\n")
                    self.assertEqual([p.name for p in (root / "state").iterdir()], ["viparu"])

                # Switching variants must not bypass existing user-edit protection.
                path = config / "gtk.css"
                path.unlink()
                path.write_text("user edit\n", encoding="utf-8")
                for action in ("--update", "--uninstall"):
                    run("nile-blue", action, success=False)
                    self.assertEqual(path.read_text(), "user edit\n")
                path.unlink()
                recorded = state / "installed/gtk.css"
                if recorded.is_symlink():
                    path.symlink_to(recorded.readlink())
                else:
                    shutil.copy2(recorded, path)
                run("nile-blue", "--uninstall")
                for name, content in originals.items():
                    self.assertEqual((config / name).read_text(), content)
                    self.assertFalse((config / name).is_symlink())
                self.assertFalse((config / "assets/variant.svg").exists())
                self.assertFalse(state.exists())
                self.assertEqual((config / "settings.ini").read_text(), "[Settings]\n")

    def test_new_and_legacy_state_preserve_original_backups(self):
        for legacy in (False, True):
            with self.subTest(legacy=legacy), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                config = root / "config/gtk-4.0"
                config.mkdir(parents=True)
                original = "/* original user stylesheet */\n"
                (config / "gtk.css").write_text(original, encoding="utf-8")
                environment = os.environ.copy()
                environment.update(XDG_CONFIG_HOME=str(root / "config"),
                                   XDG_STATE_HOME=str(root / "state"))

                def run(action):
                    result = subprocess.run(
                        ["bash", str(ROOT / "install-gtk.sh"), action],
                        env=environment, capture_output=True, text=True, timeout=10,
                    )
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    return result.stdout

                run("--copy")
                state = root / "state/viparu/gtk-4.0"
                self.assertEqual((state / "previous/gtk.css").read_text(), original)
                if legacy:
                    earlier = root / "state/vintage-pop-art-unified/gtk-4.0"
                    earlier.parent.mkdir()
                    state.rename(earlier)
                    state = earlier
                self.assertIn(f"Original backups: {state}/previous", run("--status"))
                run("--update")
                self.assertEqual((state / "previous/gtk.css").read_text(), original)
                run("--uninstall")
                self.assertEqual((config / "gtk.css").read_text(), original)
                self.assertFalse((config / "gtk-dark.css").exists())
                self.assertFalse((config / "assets").exists())


if __name__ == "__main__":
    unittest.main()
