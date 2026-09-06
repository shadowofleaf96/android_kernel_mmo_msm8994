#!/usr/bin/env python3
from __future__ import annotations

import struct
import sys
from pathlib import Path


def u16(d, o):
    return struct.unpack_from("<H", d, o)[0]


def u32(d, o):
    return struct.unpack_from("<I", d, o)[0]


def va2off(va):
    if va >= 0x4000:
        return va - 0x1000
    return va


def dump_setting(d, va, label):
    o = va2off(va)
    ptr = u32(d, o)
    a = u16(d, o + 4)
    b = u16(d, o + 6)
    c = u32(d, o + 8)
    e = u16(d, o + 12)
    f = u16(d, o + 14)
    print(
        f"{label} va=0x{va:04x} ptr=0x{ptr:04x} u16={a}/{b} u32@8={c} u16@12={e}/{f} raw={d[o:o+16].hex()}"
    )
    if 0x2000 <= ptr < 0x7000:
        po = va2off(ptr)
        n = a if 0 < a < 400 else 8
        print(f"  first {min(n,8)} regs (as addr,data,delay8):")
        for i in range(min(n, 8)):
            aa, dd, dl = u16(d, po + i * 8), u16(d, po + i * 8 + 2), u32(d, po + i * 8 + 4)
            print(f"    0x{aa:04x}=0x{dd:04x} dly={dl}")
        print(f"  first {min(n,8)} regs (as addr,data 4):")
        for i in range(min(n, 8)):
            aa, dd = u16(d, po + i * 4), u16(d, po + i * 4 + 2)
            print(f"    0x{aa:04x}=0x{dd:04x}")


def find_ptr(d, target):
    hits = []
    for i in range(0, len(d) - 3, 4):
        if u32(d, i) == target:
            hits.append(i)
    return hits


def main():
    d = Path(sys.argv[1]).read_bytes()
    print("file", sys.argv[1], "len", len(d))

    # relocated setting-like pointers
    for va in [
        0x4780,
        0x4794,
        0x47A8,
        0x47BC,
        0x4AD0,
        0x4AE4,
        0x4AF8,
        0x4B0C,
        0x4B20,
        0x4B9C,
        0x4BB0,
        0x4BC4,
    ]:
        if va2off(va) + 16 <= len(d):
            dump_setting(d, va, "set")

    print("\n=== search sizes 291/0x123, 200-400 ===")
    for i in range(0, len(d) - 1, 2):
        v = u16(d, i)
        if v == 291:
            print(f"  291 at file 0x{i:04x} va 0x{i+0x1000 if i>=0x3000 else i:04x}")

    print("\n=== pointers to 0x5918 / 0x4918 ===")
    for t in (0x5918, 0x4918, 0x5808, 0x57D8, 0x5AF0):
        hits = find_ptr(d, t)
        print(f"  0x{t:04x}: {[hex(h if h<0x3000 else h+0x1000) for h in hits]}")

    print("\n=== dump 0x4760-0x4C40 as words ===")
    start, end = 0x3760, 0x3C40  # file offs for va 0x4760-0x4C40
    for o in range(start, end, 16):
        print(f"{o+0x1000:04x} {d[o:o+16].hex()}")

    print("\n=== dump 0x57D0-0x5A00 ===")
    start, end = 0x47D0, 0x4A00
    for o in range(start, min(end, len(d)), 16):
        print(f"{o+0x1000:04x} {d[o:o+16].hex()}")


if __name__ == "__main__":
    main()
