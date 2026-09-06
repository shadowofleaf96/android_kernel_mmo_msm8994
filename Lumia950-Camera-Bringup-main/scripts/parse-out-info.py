#!/usr/bin/env python3
from __future__ import annotations

from kernel_tree import kernel_tree, overlay_root
KERNEL_TREE = kernel_tree()
OVERLAY = overlay_root()

import struct
from pathlib import Path

d = (OVERLAY / "out/libmmcamera_imx377.smia2.so").read_bytes()


def u16(o):
    return struct.unpack_from("<H", d, o)[0]


def u32(o):
    return struct.unpack_from("<I", d, o)[0]


print("=== region 0x5600-0x5780 ===")
for o in range(0x4600, 0x4780, 16):
    print(f"{o+0x1000:04x} {d[o:o+16].hex()}")

print("\n=== plausible wxh pairs as consecutive u32 ===")
for o in range(0x3000, 0x5230 - 8, 4):
    w, h = u32(o), u32(o + 4)
    if 320 <= w <= 6000 and 240 <= h <= 5000 and w >= h:
        print(f"  va 0x{o+0x1000:04x} {w}x{h}")
