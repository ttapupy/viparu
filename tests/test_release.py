"""Release naming and isolated installer-state regressions; no desktop changes."""

import configparser
import importlib.util
import os
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
SPEC.loader.exec_module(package)


class ReleaseTests(unittest.TestCase):
    def test_theme_identity_matches_release_name(self):
        metadata = configparser.ConfigParser()
        metadata.read(ROOT / "index.theme")
        self.assertEqual(package.NAME, "Viparu")
        self.assertEqual(metadata["Desktop Entry"]["Name"], package.NAME)
        self.assertEqual(metadata["X-GNOME-Metatheme"]["GtkTheme"], package.NAME)

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

    def test_archive_name_is_independent_of_checkout_directory(self):
        with tempfile.TemporaryDirectory(prefix="unrelated-checkout-") as directory:
            root = Path(directory)
            for name in package.FILES:
                (root / name).write_text("fixture\n", encoding="utf-8")
            for name in package.DIRECTORIES:
                (root / name).mkdir()
            hidden = root / "gnome-shell/.build"
            hidden.mkdir()
            (hidden / "private.scss").write_text("private", encoding="utf-8")
            with patch.object(package, "ROOT", root), \
                    patch.object(package.subprocess, "run") as build, \
                    patch.object(sys, "argv", ["package-theme.py"]):
                self.assertEqual(package.main(), 0)
                build.assert_called_once()
            with tarfile.open(root / "dist/Viparu.tar.gz") as archive:
                members = archive.getmembers()
                self.assertEqual(len(members), len(package.FILES))
                self.assertTrue(all(member.name.startswith("Viparu/") for member in members))
                self.assertEqual(archive.getmember("Viparu/install-gtk.sh").mode, 0o755)
                self.assertTrue(all(member.uid == member.gid == 0 for member in members))


@unittest.skipIf(os.geteuid() == 0, "The user installer must not run as root")
class InstallerStateTests(unittest.TestCase):
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
