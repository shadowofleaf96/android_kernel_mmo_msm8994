#!/usr/bin/env python3
from __future__ import annotations

import struct
import sys
from pathlib import Path


def u16(d, o):
    return struct.unpack_from("<H", d, o)[0]


def u32(d, o):
    return struct.unpack_from("<I", d, o)[0]


def va2off(va, dlen):
    if 0x4000 <= va < 0x4000 + 0x3000:
        off = va - 0x1000
        if 0 <= off + 8 <= dlen:
            return off
    if 0x271C <= va < 0x2A60:
        return va
    return None


def main():
    d = Path(sys.argv[1]).read_bytes()
    print("file", sys.argv[1])
    print("=== 20-byte I2C settings (ptr,size,addr=2,data=1) ===")
    for o in range(0x3000, min(len(d) - 20, 0x5230), 4):
        ptr = u32(d, o)
        size = u32(d, o + 4)
        at = u32(d, o + 8)
        dt = u32(d, o + 12)
        delay = u32(d, o + 16)
        po = va2off(ptr, len(d))
        if po is None:
            continue
        if not (1 <= size <= 400 and at in (1, 2, 3) and dt in (1, 2, 3) and delay <= 200):
            continue
        a0, d0 = u16(d, po), u16(d, po + 2)
        print(
            f"  va 0x{o+0x1000:04x} ptr=0x{ptr:04x} n={size:3d} "
            f"addr={at} data={dt} dly={delay} first=0x{a0:04x}=0x{d0:04x}"
        )

    print("\n=== interesting u16 dimensions ===")
    interesting = {
        4056,
        3040,
        2028,
        1520,
        1920,
        1080,
        1280,
        720,
        2592,
        1944,
        2560,
        1440,
        4992,
        3744,
        5344,
        4016,
        4224,
        3136,
        5248,
        3936,
        4160,
        3120,
        2096,
        1560,
        1632,
        1224,
        3264,
        2448,
        4208,
        3120,
        2016,
        1504,
        1048,
        780,
        640,
        480,
        5693,
        377,
    }
    seen = {}
    for o in range(0, len(d) - 1, 2):
        v = u16(d, o)
        if v in interesting:
            seen.setdefault(v, []).append(o)
    for v, offs in sorted(seen.items()):
        print(f"  {v:5d} x{len(offs)} first={[hex(x) for x in offs[:8]]}")

    print("\n=== rodata strings ===")
    s = d[0x271C:0x2A59]
    cur = []
    start = 0x271C
    for i, b in enumerate(s):
        if 32 <= b < 127:
            cur.append(chr(b))
        else:
            if len(cur) >= 4:
                print(f"  0x{start+i-len(cur):04x} {''.join(cur)}")
            cur = []


if __name__ == "__main__":
    main()
