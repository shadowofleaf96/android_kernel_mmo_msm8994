#!/usr/bin/env python3
from __future__ import annotations

import struct
import sys
from pathlib import Path


def u16(d, o):
    return struct.unpack_from("<H", d, o)[0]


def u32(d, o):
    return struct.unpack_from("<I", d, o)[0]


def main():
    d = Path(sys.argv[1]).read_bytes()
    print("file", sys.argv[1], "len", len(d))
    targets = {
        4032,
        3024,
        4000,
        3000,
        3840,
        2160,
        2592,
        1944,
        5344,
        4016,
        2600,
        1952,
        4208,
        3120,
        4056,
        3040,
        3288,
        2480,
    }
    print("=== u16 hits ===")
    for o in range(0, len(d) - 1, 2):
        v = u16(d, o)
        if v in targets:
            nxt = u16(d, o + 2) if o + 4 <= len(d) else 0
            print(f"  file 0x{o:04x} va 0x{(o+0x1000 if o>=0x3000 else o):04x} {v} next_u16={nxt}")

    print("=== dump va 0x4640-0x4760 ===")
    for o in range(0x3640, 0x3760, 16):
        print(f"{o+0x1000:04x} {d[o:o+16].hex()}")

    print("=== dump va 0x4C40-0x4E00 ===")
    for o in range(0x3C40, 0x3E00, 16):
        print(f"{o+0x1000:04x} {d[o:o+16].hex()}")


if __name__ == "__main__":
    main()
