#!/usr/bin/env python3
"""Rebuild and package standalone variants, including sources and licenses."""

import argparse
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

from theme_variants import DIRECTORIES, FILES, load_variants, project_files

ROOT = Path(__file__).resolve().parents[1]


def package_files(root=None):
    return project_files(ROOT if root is None else root)


def archive_metadata(info):
    # Do not publish local account names or restrictive development permissions.
    info.uid = info.gid = 0
    info.uname = info.gname = ""
    info.mode = 0o755 if info.mode & 0o111 or info.name.endswith("/install-gtk.sh") else 0o644
    info.pax_headers = {}
    return info


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variant", metavar="ID", help="Package only this variant (default: all)")
    args = parser.parse_args()
    try:
        variants = load_variants(ROOT)
        keys = [args.variant] if args.variant else list(variants)
        if any(key not in variants for key in keys):
            raise ValueError(f"Unknown theme variant: {args.variant!r}")
        selection = ["--variant", args.variant] if args.variant else ["--variants"]
        subprocess.run(
            [sys.executable, "-B", str(ROOT / "scripts/build-theme.py"), *selection],
            cwd=ROOT, check=True, timeout=600,
        )
        for key in keys:
            name = variants[key]["name"]
            theme = ROOT / "dist/themes" / name
            files = package_files(theme)
            destination = ROOT / "dist" / f"{name}.tar.gz"
            with tempfile.TemporaryDirectory(prefix=".package-", dir=destination.parent) as directory:
                staging = Path(directory) / destination.name
                with tarfile.open(staging, "w:gz", format=tarfile.PAX_FORMAT) as archive:
                    for path in files:
                        archive.add(
                            path, arcname=f"{name}/{path.relative_to(theme).as_posix()}",
                            recursive=False, filter=archive_metadata,
                        )
                staging.replace(destination)
            print(f"Packaged {len(files)} files: {destination.relative_to(ROOT)}")
        print("No installation, desktop settings changes or test suites were run.")
    except (OSError, ValueError, RuntimeError, tarfile.TarError, subprocess.SubprocessError) as error:
        print(f"Theme packaging failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
