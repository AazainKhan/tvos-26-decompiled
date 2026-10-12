#!/usr/bin/env python3
"""Turn class-dump headers into name-level TSV indexes.

Usage: index_headers.py <headers_dir> <out_dir>

For each image directory under <headers_dir> writes:
  <out_dir>/<image>.classes.tsv  kind, name, superclass, protocols
  <out_dir>/<image>.members.tsv  owner, kind (+ / - / property), declaration
Only interface declarations are kept; no implementation exists in headers.
"""
import re
import sys
from pathlib import Path

DECL = re.compile(r"^@(interface|protocol)\s+(\w+)(?:\s*\((\w*)\))?(?:\s*:\s*(\w+))?(?:\s*<([^>]*)>)?")
MEMBER = re.compile(r"^([+-])\s*\(.*")
PROP = re.compile(r"^@property\b.*;")


def clean(line: str) -> str:
    line = re.sub(r"//.*$", "", line).strip()
    return re.sub(r"\s+", " ", line)


def index_image(img_dir: Path, out_dir: Path) -> tuple[int, int]:
    classes, members = [], []
    for h in sorted(img_dir.rglob("*.h")):
        owner = None
        for raw in h.read_text(errors="replace").splitlines():
            line = clean(raw)
            if not line:
                continue
            m = DECL.match(line)
            if m:
                kind, name, category, sup, protos = m.groups()
                if category is not None:
                    kind = "category"
                    name = f"{name}({category})"
                owner = name
                protos = ",".join(p.strip() for p in (protos or "").split(",") if p.strip())
                classes.append((kind, name, sup or "", protos))
                continue
            if line.startswith("@end"):
                owner = None
                continue
            if owner is None:
                continue
            if PROP.match(line):
                members.append((owner, "property", line))
            elif MEMBER.match(line) and line.endswith(";"):
                members.append((owner, line[0], line))
    name = img_dir.name
    with open(out_dir / f"{name}.classes.tsv", "w") as f:
        f.write("kind\tname\tsuperclass\tprotocols\n")
        for row in sorted(set(classes)):
            f.write("\t".join(row) + "\n")
    with open(out_dir / f"{name}.members.tsv", "w") as f:
        f.write("owner\tkind\tdeclaration\n")
        for row in sorted(set(members)):
            f.write("\t".join(row) + "\n")
    return len(set(classes)), len(set(members))


def main() -> None:
    src, out = Path(sys.argv[1]), Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    for img in sorted(p for p in src.iterdir() if p.is_dir()):
        c, m = index_image(img, out)
        print(f"{img.name}\t{c} types\t{m} members")


if __name__ == "__main__":
    main()
