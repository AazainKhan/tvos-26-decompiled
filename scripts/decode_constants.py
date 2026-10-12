#!/usr/bin/env python3
"""Decode the numbers that constant-returning ObjC methods produce, from `ipsw dyld disass` output.

Usage: decode_constants.py <image.s> <out.tsv> [class_regex]

For every method of a matching class it follows mov/movk into x registers, fmov into d registers
(register moves and float immediates), and fcsel. Output columns:
  method, returns (value or "a if <cond> else b"), condition selector, all float constants seen.
Only numbers are written; no instructions are copied.
"""
import re
import struct
import sys

HEAD = re.compile(r"^([+-]\[[^\]]+\]):")
INS = re.compile(r"^0x[0-9a-f]+:\s+(?:[0-9a-f]{2} ){4}\s*(\w+)\s*(.*)$")


def f64(bits: int) -> float:
    return struct.unpack("<d", struct.pack("<Q", bits & 0xFFFFFFFFFFFFFFFF))[0]


def fmt(v: float) -> str:
    return f"{v:g}"


def decode(lines: list[str]) -> tuple[str, str, list[str]]:
    x: dict[str, int] = {}
    d: dict[str, str] = {}
    seen: list[str] = []
    cond_sel = ""
    for line in lines:
        m = INS.match(line.strip())
        if not m:
            continue
        op, args = m.group(1), m.group(2)
        a = [s.strip() for s in args.split(",")]
        if "objc_msgSend" in args:
            s = re.search(r'"([^"]+)"', args)
            if s:
                cond_sel = s.group(1)
        if op == "mov" and len(a) == 2 and a[0].startswith("x") and a[1].startswith("#"):
            try:
                x[a[0]] = int(a[1][1:], 0)
            except ValueError:
                pass
        elif op == "movk" and len(a) >= 2 and a[0] in x:
            imm = int(a[1][1:], 0)
            shift = int(a[2].split("#")[1], 0) if len(a) > 2 and "lsl" in a[2] else 0
            x[a[0]] = (x[a[0]] & ~(0xFFFF << shift)) | (imm << shift)
        elif op == "fmov" and len(a) == 2 and a[0].startswith(("d", "s")):
            src = a[1]
            if src.startswith("x") and src in x:
                v = fmt(f64(x[src]))
            elif src.startswith("#"):
                try:
                    v = fmt(float(src[1:]))
                except ValueError:
                    continue
            elif src in d:
                v = d[src]
            else:
                continue
            d["d" + a[0][1:]] = v
            seen.append(v)
        elif op in ("movi", "fmov") and len(a) == 2 and a[1] in ("#0", "#0.0"):
            d["d" + a[0][1:]] = "0"
        elif op == "fcsel" and len(a) == 4:
            t, f = d.get(a[1], "?"), d.get(a[2], "?")
            d["d" + a[0][1:]] = f"{t} if {a[3]} else {f}"
        elif op == "ret":
            break
    return d.get("d0", ""), cond_sel, seen


def main() -> None:
    src, out = sys.argv[1], sys.argv[2]
    cls = re.compile(sys.argv[3]) if len(sys.argv) > 3 else None
    funcs: dict[str, list[str]] = {}
    cur = None
    for line in open(src, errors="replace"):
        h = HEAD.match(line)
        if h:
            cur = h.group(1)
            funcs[cur] = []
        elif cur:
            funcs[cur].append(line)
    rows = 0
    with open(out, "w") as f:
        f.write("method\treturns\tcondition_selector\tconstants_seen\n")
        for name, body in sorted(funcs.items()):
            owner = name[2:].split(" ")[0]
            if cls and not cls.search(owner):
                continue
            ret, sel, seen = decode(body)
            if not seen and not ret:
                continue
            f.write(f"{name}\t{ret}\t{sel}\t{','.join(dict.fromkeys(seen))}\n")
            rows += 1
    print(f"{rows} methods with float constants")


if __name__ == "__main__":
    main()
