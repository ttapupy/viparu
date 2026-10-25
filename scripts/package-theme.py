#!/usr/bin/env python3
"""Rebuild and package the theme, sources and licenses without private development data."""

import argparse
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAME = "Viparu"
FILES = (
    "README.md", "USAGE.md", "DEVELOPMENT.md", "THIRD_PARTY.md", "LICENSE",
    "index.theme", "install-gtk.sh", "color-palette.json", "color-palette.scss",
)
DIRECTORIES = (
    "assets", "common", "gnome-shell", "gtk-3.0", "gtk-4.0", "licenses",
    "scripts", "scss", "tests",
)


def package_files():
    files = []
    for name in FILES + DIRECTORIES:
        source = ROOT / name
        if source.is_symlink() or not source.exists():
            raise ValueError(f"Missing package input or unsupported symlink: {name}")
        paths = sorted(source.rglob("*")) if source.is_dir() else [source]
        for path in paths:
            relative = path.relative_to(ROOT)
            if any(part.startswith(".") or part == "__pycache__" for part in relative.parts):
                continue
            if path.suffix in (".pyc", ".pyo"):
                continue
            if path.is_symlink():
                raise ValueError(f"Symlinks are not allowed in package inputs: {relative}")
            if path.is_file():
                files.append(path)
    return sorted(files)


def archive_metadata(info):
    # Do not publish local account names or restrictive development permissions.
    info.uid = info.gid = 0
    info.uname = info.gname = ""
    info.mode = 0o755 if info.mode & 0o111 or info.name == f"{NAME}/install-gtk.sh" else 0o644
    info.pax_headers = {}
    return info


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    try:
        subprocess.run(
            [sys.executable, "-B", str(ROOT / "scripts/build-theme.py")],
            cwd=ROOT, check=True, timeout=300,
        )
        files = package_files()
        destination = ROOT / "dist" / f"{NAME}.tar.gz"
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".package-", dir=destination.parent) as directory:
            staging = Path(directory) / destination.name
            with tarfile.open(staging, "w:gz", format=tarfile.PAX_FORMAT) as archive:
                for path in files:
                    archive.add(
                        path, arcname=f"{NAME}/{path.relative_to(ROOT).as_posix()}",
                        recursive=False, filter=archive_metadata,
                    )
            staging.replace(destination)
        print(f"Packaged {len(files)} files: {destination.relative_to(ROOT)}")
        print("No installation, desktop settings changes or test suites were run.")
    except (OSError, ValueError, tarfile.TarError, subprocess.SubprocessError) as error:
        print(f"Theme packaging failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
