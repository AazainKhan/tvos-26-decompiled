#!/usr/bin/env python3
"""Put ObjC method names back on a stripped app's disassembly.

Usage: relabel_stripped.py <classdump_re.txt> <in.s> <out.s> [base]

<classdump_re.txt> is `ipsw class-dump <macho> --re -V` output, where each method follows a
`// 0x<offset>` comment. <in.s> is `ipsw macho disass <macho> --section __TEXT.__text` output,
whose functions are labelled `sub_<vaddr>:`. Labels that match a method become `-[Class sel]:`.
"""
import re
import sys

IFACE = re.compile(r"^@interface (\w+)(?: \((\w*)\))?")
ADDR = re.compile(r"^// (0x[0-9a-f]+)\s*$")
METHOD = re.compile(r"^([+-]) \([^)]*\)(.*);")


def selector(rest: str) -> str:
    parts = re.findall(r"(\w+):", re.sub(r"\([^)]*\)", "", rest))
    return "".join(p + ":" for p in parts) if parts else rest.strip().split()[0]


def main() -> None:
    dump, src, out = sys.argv[1], sys.argv[2], sys.argv[3]
    base = int(sys.argv[4], 0) if len(sys.argv) > 4 else 0x100000000
    names: dict[int, str] = {}
    cls, pending = None, None
    for line in open(dump, errors="replace"):
        line = line.rstrip("\n")
        m = IFACE.match(line)
        if m:
            cls = m.group(1)
            continue
        if line.startswith("@end"):
            cls = None
            continue
        a = ADDR.match(line)
        if a:
            pending = int(a.group(1), 16)
            continue
        mm = METHOD.match(line)
        if mm and cls and pending is not None:
            names.setdefault(base + pending, f"{mm.group(1)}[{cls} {selector(mm.group(2))}]")
        pending = None
    hits = 0
    with open(out, "w") as f:
        for line in open(src, errors="replace"):
            m = re.match(r"^sub_([0-9a-f]+):", line)
            if m and int(m.group(1), 16) in names:
                line = names[int(m.group(1), 16)] + ":\n"
                hits += 1
            f.write(line)
    print(f"{len(names)} methods known, {hits} functions relabelled")


if __name__ == "__main__":
    main()
