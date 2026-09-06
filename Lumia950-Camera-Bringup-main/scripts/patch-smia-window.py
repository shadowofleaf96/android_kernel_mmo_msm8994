#!/usr/bin/env python3
"""smia5: BYTE-write a VFE-safe SMIA crop after the existing 0x0103 reset.

Window registers are 16-bit big-endian. Write them as two BYTE ops so we
stay on the smia2 data_type=1 setting (ov5693 init is a 1-element list).
Keep original IMX377/OV5693 out_info sizes — 5344-wide exceeds this VFE.
"""
from __future__ import annotations

import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def u16(d, o):
    return struct.unpack_from("<H", d, o)[0]


def u32(d, o):
    return struct.unpack_from("<I", d, o)[0]


def p16(d, o, v):
    struct.pack_into("<H", d, o, v)


def p32(d, o, v):
    struct.pack_into("<I", d, o, v)


def va2off(va):
    if 0x4000 <= va < 0x7000:
        return va - 0x1000
    return None


def write_reg(d, arr_off, addr, data, delay=0):
    p16(d, arr_off, addr)
    p16(d, arr_off + 2, data)
    p32(d, arr_off + 4, delay)


def byte_window(x0, y0, w, h):
    x1, y1 = x0 + w - 1, y0 + h - 1
    regs = []
    for addr, val in (
        (0x0344, x0),
        (0x0346, y0),
        (0x0348, x1),
        (0x034A, y1),
        (0x034C, w),
        (0x034E, h),
    ):
        regs.append((addr, (val >> 8) & 0xFF))
        regs.append((addr + 1, val & 0xFF))
    return regs


def patch_one(d: bytearray, name: str, window) -> None:
    reset = None
    res_holds = []
    for o in range(0x3000, min(len(d) - 20, 0x5230), 4):
        ptr = u32(d, o)
        size = u32(d, o + 4)
        at = u32(d, o + 8)
        dt = u32(d, o + 12)
        delay = u32(d, o + 16)
        po = va2off(ptr)
        if po is None or not (size == 1 and at == 2 and dt == 1 and delay <= 200):
            continue
        a0, d0 = u16(d, po), u16(d, po + 2)
        if a0 == 0x0103 and d0 == 1:
            reset = (o, ptr, po)
        elif a0 == 0x0104 and d0 == 1 and o >= 0x3B00:
            res_holds.append(po)

    if reset is None:
        raise SystemExit(f"{name}: no SMIA reset setting")
    o, ptr, po = reset
    regs = byte_window(*window)
    write_reg(d, po, 0x0103, 1, 50)
    for i, (addr, data) in enumerate(regs, start=1):
        write_reg(d, po + i * 8, addr, data, 0)
    p32(d, o + 4, 1 + len(regs))
    print(
        f"  {name} init n={1+len(regs)} crop {window[2]}x{window[3]} "
        f"origin {window[0]},{window[1]} ptr=0x{ptr:04x}"
    )
    for po_h in res_holds:
        write_reg(d, po_h, 0x0104, 0, 0)
    if res_holds:
        print(f"  {name} cleared {len(res_holds)} res grouped-hold writes")


def main():
    out = ROOT / "out"
    mag = out / "magisk-talkman-smia" / "system" / "vendor" / "lib"
    mag.mkdir(parents=True, exist_ok=True)

    d = bytearray((out / "libmmcamera_imx377.smia2.so").read_bytes())
    patch_one(d, "imx377", (632, 494, 4080, 3028))
    (out / "libmmcamera_imx377.smia5.so").write_bytes(d)
    (mag / "libmmcamera_imx377.so").write_bytes(d)

    d = bytearray((out / "libmmcamera_ov5693.smia2.so").read_bytes())
    patch_one(d, "ov5693", (4, 4, 2592, 1944))
    (out / "libmmcamera_ov5693.smia5.so").write_bytes(d)
    (mag / "libmmcamera_ov5693.so").write_bytes(d)
    print("wrote smia5")


if __name__ == "__main__":
    main()
