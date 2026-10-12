#!/usr/bin/env python3
"""Index animation timing from CoreAnimation .ca packages (CAML XML).

Usage: index_caml.py <mounted_root> <out.tsv>

Walks <mounted_root> for *.ca/main.caml and records, per animation element:
file, layer, element, keyPath, duration, beginTime, repeatCount, autoreverses,
timing function, and spring parameters (mass, stiffness, damping,
initialVelocity) when present. Values only; no artwork is copied.
"""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ATTRS = ["keyPath", "duration", "beginTime", "repeatCount", "autoreverses",
         "mass", "stiffness", "damping", "initialVelocity", "fillMode", "speed"]


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def timing_of(el: ET.Element) -> str:
    fns = []
    for d in el.iter():
        if local(d.tag) == "CAMediaTimingFunction":
            fns.append(" ".join(f"{k}={v}" for k, v in sorted(d.attrib.items())) or "default")
    return "|".join(fns) or el.get("timingFunction", "")


def series(el: ET.Element, name: str) -> str:
    for child in el:
        if local(child.tag) == name:
            return ",".join(v.get("value", "") for v in child if v.get("value") is not None)
    return ""


def walk(path: Path, root_dir: Path, rows: list) -> None:
    try:
        tree = ET.parse(path)
    except ET.ParseError:
        return
    rel = str(path.parent.relative_to(root_dir))

    def visit(el: ET.Element, layer: str) -> None:
        tag = local(el.tag)
        if tag == "CALayer" or tag.endswith("Layer"):
            layer = el.get("name") or el.get("id") or layer
        # CAML writes animations as <animation type="CABasicAnimation" ...>.
        anim_type = el.get("type", "") if tag == "animation" else (tag if tag.endswith("Animation") else "")
        if anim_type:
            row = ([rel, layer, anim_type] + [el.get(a, "") for a in ATTRS]
                   + [timing_of(el), series(el, "keyTimes"), series(el, "values")])
            if any(row[3:]):
                rows.append(row)
        for child in el:
            visit(child, layer)

    visit(tree.getroot(), "")


def main() -> None:
    root_dir, out = Path(sys.argv[1]), Path(sys.argv[2])
    rows: list = []
    for caml in sorted(root_dir.rglob("*.ca/main.caml")):
        if "/Caches/" in str(caml):
            continue
        walk(caml, root_dir, rows)
    with open(out, "w") as f:
        f.write("\t".join(["package", "layer", "type"] + ATTRS + ["timingFunctions", "keyTimes", "values"]) + "\n")
        for r in rows:
            f.write("\t".join(v.replace("\t", " ") for v in r) + "\n")
    print(f"{len(rows)} animations from {len({r[0] for r in rows})} packages")


if __name__ == "__main__":
    main()
