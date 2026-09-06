#!/usr/bin/env python3
"""smia7: smia2 I2C + VFE-safe sizes (4080x3028 rear) + live SMIA clocks.

Open Camera picked 5344x4008 preview from smia6 and the MSM8992 VFE hung.
Advertise the IMX377-class window the kernel now crops Hill to.
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


def patch_wh_pairs(d: bytearray, old_w: int, old_h: int, new_w: int, new_h: int,
                   name: str) -> None:
    n = 0
    for o in range(0, len(d) - 3, 2):
        if u16(d, o) == old_w and u16(d, o + 2) == old_h:
            p16(d, o, new_w)
            p16(d, o + 2, new_h)
            n += 1
            print(f"  {name} u16 {old_w}x{old_h} -> {new_w}x{new_h} @ 0x{o:04x}")
    for o in range(0, len(d) - 7, 4):
        if u32(d, o) == old_w and u32(d, o + 4) == old_h:
            p32(d, o, new_w)
            p32(d, o + 4, new_h)
            n += 1
            print(f"  {name} u32 {old_w}x{old_h} -> {new_w}x{new_h} @ 0x{o:04x}")
    print(f"  {name} replaced {n} size slots")


def patch_mode0(d: bytearray, name: str, w: int, h: int, llp: int, fll: int) -> None:
    print(f"  {name} mode0 {u16(d, 0x3C88)}x{u16(d, 0x3C8A)} llp={u16(d, 0x3C8C)} fll={u16(d, 0x3C8E)}")
    p16(d, 0x3C88, w)
    p16(d, 0x3C8A, h)
    p16(d, 0x3C8C, llp)
    p16(d, 0x3C8E, fll)
    p32(d, 0x3688, w)
    p32(d, 0x368C, h)


def main():
    out = ROOT / "out"
    mag = out / "magisk-talkman-smia" / "system" / "vendor" / "lib"
    mag.mkdir(parents=True, exist_ok=True)
    root_mod = out / "magisk-talkman-smia"
    root_mod.mkdir(parents=True, exist_ok=True)

    d = bytearray((out / "libmmcamera_imx377.smia2.so").read_bytes())
    patch_wh_pairs(d, 5344, 4016, 4080, 3028, "imx377")
    patch_mode0(d, "imx377", 4080, 3028, 6024, 4106)
    patch_clocks(d, 461000000, 53100000, "imx377")
    (out / "libmmcamera_imx377.smia7.so").write_bytes(d)
    (mag / "libmmcamera_imx377.so").write_bytes(d)
    (root_mod / "libmmcamera_imx377.so").write_bytes(d)

    d = bytearray((out / "libmmcamera_ov5693.smia2.so").read_bytes())
    patch_mode0(d, "ov5693", 2600, 1952, 2750, 2084)
    patch_clocks(d, 160000000, 127680000, "ov5693")
    (out / "libmmcamera_ov5693.smia7.so").write_bytes(d)
    (mag / "libmmcamera_ov5693.so").write_bytes(d)
    (root_mod / "libmmcamera_ov5693.so").write_bytes(d)
    print("wrote smia7")


if __name__ == "__main__":
    main()
