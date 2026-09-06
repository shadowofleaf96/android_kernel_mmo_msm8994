#!/usr/bin/env python3
"""smia6: keep smia2 BYTE I2C, advertise live SMIA windows and pixel clocks.

Kernel #7 CFG_STREAM matches. VFE still gets IMX377 4080x3028 @ 461 MHz
while the Sharp sensors stream 5344x4016 @ 53.1 MHz and 2600x1952 @ 127.7 MHz.
"""
from __future__ import annotations

import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def p16(d, o, v):
    struct.pack_into("<H", d, o, v)


def p32(d, o, v):
    struct.pack_into("<I", d, o, v)


def u16(d, o):
    return struct.unpack_from("<H", d, o)[0]


def u32(d, o):
    return struct.unpack_from("<I", d, o)[0]


def patch_clocks(d: bytearray, old: int, new: int, name: str) -> None:
    n = 0
    for o in range(0, len(d) - 4, 4):
        if u32(d, o) == old:
            p32(d, o, new)
            n += 1
            print(f"  {name} clk 0x{o:04x} {old} -> {new}")
    if n == 0:
        raise SystemExit(f"{name}: clock {old} not found")


def patch_mode0(d: bytearray, name: str, w: int, h: int, llp: int, fll: int) -> None:
    print(f"  {name} mode0 {u16(d, 0x3C88)}x{u16(d, 0x3C8A)} llp={u16(d, 0x3C8C)} fll={u16(d, 0x3C8E)}")
    p16(d, 0x3C88, w)
    p16(d, 0x3C8A, h)
    p16(d, 0x3C8C, llp)
    p16(d, 0x3C8E, fll)
    print(f"  {name} active {u32(d, 0x3688)}x{u32(d, 0x368C)} -> {w}x{h}")
    p32(d, 0x3688, w)
    p32(d, 0x368C, h)


def main():
    out = ROOT / "out"
    mag = out / "magisk-talkman-smia" / "system" / "vendor" / "lib"
    mag.mkdir(parents=True, exist_ok=True)

    d = bytearray((out / "libmmcamera_imx377.smia2.so").read_bytes())
    patch_mode0(d, "imx377", 5344, 4016, 6024, 4106)
    patch_clocks(d, 461000000, 53100000, "imx377")
    (out / "libmmcamera_imx377.smia6.so").write_bytes(d)
    (mag / "libmmcamera_imx377.so").write_bytes(d)

    d = bytearray((out / "libmmcamera_ov5693.smia2.so").read_bytes())
    patch_mode0(d, "ov5693", 2600, 1952, 2750, 2084)
    patch_clocks(d, 160000000, 127680000, "ov5693")
    (out / "libmmcamera_ov5693.smia6.so").write_bytes(d)
    (mag / "libmmcamera_ov5693.so").write_bytes(d)
    print("wrote smia6")


if __name__ == "__main__":
    main()
