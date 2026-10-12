#!/usr/bin/env python3
"""Inventory apps and frameworks in a mounted tvOS root filesystem.

Usage: index_bundles.py <mounted_root> <out_dir>

Writes:
  apps.tsv        path, bundle id, executable, min OS, URL schemes, size (bytes)
  frameworks.tsv  path, bundle id, has resources (Assets.car / .ca), in dyld cache
  ca-packages.txt every .ca / .caar package path
"""
import plistlib
import sys
from pathlib import Path


def info(bundle: Path) -> dict:
    p = bundle / "Info.plist"
    try:
        with open(p, "rb") as f:
            return plistlib.load(f)
    except Exception:
        return {}


def size(bundle: Path) -> int:
    return sum(f.stat().st_size for f in bundle.rglob("*") if f.is_file() and not f.is_symlink())


def schemes(i: dict) -> str:
    out = []
    for t in i.get("CFBundleURLTypes", []) or []:
        out += t.get("CFBundleURLSchemes", []) or []
    return ",".join(sorted(set(out)))


def main() -> None:
    root, out = Path(sys.argv[1]), Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    apps = sorted((root / "Applications").glob("*.app")) + sorted((root / "System/Library/CoreServices").glob("*.app"))
    with open(out / "apps.tsv", "w") as f:
        f.write("path\tbundle_id\texecutable\tmin_os\turl_schemes\tsize_bytes\n")
        for a in apps:
            i = info(a)
            f.write("\t".join([str(a.relative_to(root)), i.get("CFBundleIdentifier", ""),
                               i.get("CFBundleExecutable", ""), i.get("MinimumOSVersion", ""),
                               schemes(i), str(size(a))]) + "\n")
    fws = []
    for base in ("System/Library/Frameworks", "System/Library/PrivateFrameworks"):
        fws += sorted((root / base).glob("*.framework"))
    with open(out / "frameworks.tsv", "w") as f:
        f.write("path\tbundle_id\thas_assets_car\tca_packages\tbinary_on_disk\n")
        for fw in fws:
            i = info(fw)
            name = fw.name.removesuffix(".framework")
            ca = len(list(fw.glob("*.ca"))) + len(list(fw.glob("*.caar")))
            f.write("\t".join([str(fw.relative_to(root)), i.get("CFBundleIdentifier", ""),
                               "yes" if (fw / "Assets.car").exists() else "no", str(ca),
                               "yes" if (fw / name).exists() else "no (dyld cache)"]) + "\n")
    with open(out / "ca-packages.txt", "w") as f:
        for p in sorted(root.rglob("*.ca")) + sorted(root.rglob("*.caar")):
            if "/Caches/" not in str(p):
                f.write(str(p.relative_to(root)) + "\n")
    print(f"{len(apps)} apps, {len(fws)} frameworks")


if __name__ == "__main__":
    main()
