#!/usr/bin/env python3
"""Index Swift type names and member names from `ipsw swift-dump` output.

Usage: index_swift.py <dump.swift> <out.tsv>

Keeps: kind, type name, conformance/superclass, and field/case names.
Drops: addresses, method bodies (none exist in the dump), imported __C types.
"""
import re
import sys

TYPE = re.compile(r"^(class|struct|enum|protocol|extension)\s+([\w.<>,\s]+?)(?:\s*:\s*([^{]+))?\s*\{")
FIELD = re.compile(r"^\s+(let|var|case)\s+(\w+)")


def main() -> None:
    src, out = sys.argv[1], sys.argv[2]
    rows, cur = [], None
    for line in open(src, errors="replace"):
        m = TYPE.match(line)
        if m:
            kind, name, conf = m.group(1), m.group(2).strip(), (m.group(3) or "").strip()
            cur = None if name.startswith("__C.") else (kind, name, conf)
            if cur:
                rows.append((kind, name, conf, "", ""))
            continue
        if line.startswith("}"):
            cur = None
            continue
        if cur:
            f = FIELD.match(line)
            if f:
                rows.append((cur[0], cur[1], cur[2], f.group(1), f.group(2)))
    with open(out, "w") as fh:
        fh.write("kind\ttype\tconformance\tmember_kind\tmember\n")
        for r in rows:
            fh.write("\t".join(r) + "\n")
    print(f"{sum(1 for r in rows if not r[3])} types, {sum(1 for r in rows if r[3])} members")


if __name__ == "__main__":
    main()
