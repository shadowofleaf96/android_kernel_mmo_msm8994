#!/usr/bin/env python3
"""Patch only advertised/out_info sizes. Leave I2C arrays as smia2 BYTE reset.

Sensor already comes up in native SMIA mode after 0x0103 reset.
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


def main():
    out = ROOT / "out"
    mag = out / "magisk-talkman-smia" / "system" / "vendor" / "lib"

    d = bytearray((out / "libmmcamera_imx377.smia2.so").read_bytes())
    print("imx377 active", u32(d, 0x3688), "x", u32(d, 0x368C))
    p32(d, 0x3688, 5344)
    p32(d, 0x368C, 4016)
    print("imx377 mode0", u16(d, 0x3C88), "x", u16(d, 0x3C8A), "llp", u16(d, 0x3C8C), "fll", u16(d, 0x3C8E))
    p16(d, 0x3C88, 5344)
    p16(d, 0x3C8A, 4016)
    p16(d, 0x3C8C, 6024)
    p16(d, 0x3C8E, 4106)
    (out / "libmmcamera_imx377.smia4.so").write_bytes(d)
    (mag / "libmmcamera_imx377.so").write_bytes(d)

    d = bytearray((out / "libmmcamera_ov5693.smia2.so").read_bytes())
    print("ov5693 active", u32(d, 0x3688), "x", u32(d, 0x368C))
    p32(d, 0x3688, 2600)
    p32(d, 0x368C, 1952)
    print("ov5693 mode0", u16(d, 0x3C88), "x", u16(d, 0x3C8A), "llp", u16(d, 0x3C8C), "fll", u16(d, 0x3C8E))
    p16(d, 0x3C88, 2600)
    p16(d, 0x3C8A, 1952)
    p16(d, 0x3C8C, 2750)
    p16(d, 0x3C8E, 2084)
    (out / "libmmcamera_ov5693.smia4.so").write_bytes(d)
    (mag / "libmmcamera_ov5693.so").write_bytes(d)
    print("wrote smia4")


if __name__ == "__main__":
    main()
