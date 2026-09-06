#!/usr/bin/env python3
"""smia8: smia7 window + Windows-like 316.8 MHz vt for Hill.

WOA camera log: MIPIDDRClock=633600000, settle=21, 4 lanes.
Kernel #12 programs SMIA PLL to that op_sys. HAL CAMIF pixclk must match vt.
"""
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]


def p32(d, o, v):
    struct.pack_into("<I", d, o, v)


def u32(d, o):
    return struct.unpack_from("<I", d, o)[0]


def patch_clocks(d, old, new, name):
    n = 0
    for o in range(0, len(d) - 4, 4):
        if u32(d, o) == old:
            p32(d, o, new)
            n += 1
            print(f"  {name} clk 0x{o:04x} {old} -> {new}")
    print(f"  {name} replaced {n} clocks")


def main():
    out = ROOT / "out"
    mag = out / "magisk-talkman-smia" / "system" / "vendor" / "lib"
    mag.mkdir(parents=True, exist_ok=True)
    root_mod = out / "magisk-talkman-smia"
    d = bytearray((out / "libmmcamera_imx377.smia7.so").read_bytes())
    patch_clocks(d, 53100000, 316800000, "imx377")
    (out / "libmmcamera_imx377.smia8.so").write_bytes(d)
    (mag / "libmmcamera_imx377.so").write_bytes(d)
    (root_mod / "libmmcamera_imx377.so").write_bytes(d)
    ov = (out / "libmmcamera_ov5693.smia7.so").read_bytes()
    (out / "libmmcamera_ov5693.smia8.so").write_bytes(ov)
    (mag / "libmmcamera_ov5693.so").write_bytes(ov)
    (root_mod / "libmmcamera_ov5693.so").write_bytes(ov)
    print("wrote smia8")


if __name__ == "__main__":
    main()
