#!/usr/bin/env python3
"""Point IMX377/OV5693 out_info at the live SMIA windows.

Must start from smia2 (ID + SMIA reset). Do not reuse a previous smia3.
"""
from __future__ import annotations

import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def p16(d: bytearray, o: int, v: int) -> None:
    struct.pack_into("<H", d, o, v)


def p32(d: bytearray, o: int, v: int) -> None:
    struct.pack_into("<I", d, o, v)


def u16(d: bytearray, o: int) -> int:
    return struct.unpack_from("<H", d, o)[0]


def u32(d: bytearray, o: int) -> int:
    return struct.unpack_from("<I", d, o)[0]


def patch_out_info(d: bytearray, off: int, x: int, y: int, llp: int, fll: int, label: str) -> None:
    print(f"  {label} @{off:04x} {u16(d, off)}x{u16(d, off+2)} llp={u16(d, off+4)} fll={u16(d, off+6)} -> {x}x{y} llp={llp} fll={fll}")
    p16(d, off, x)
    p16(d, off + 2, y)
    p16(d, off + 4, llp)
    p16(d, off + 6, fll)


def patch_res_window(d: bytearray, setting_off: int, regs: list[tuple[int, int]]) -> None:
    ptr = u32(d, setting_off)
    po = ptr - 0x1000
    p32(d, setting_off + 4, len(regs))
    p32(d, setting_off + 8, 2)  # WORD addr
    p32(d, setting_off + 12, 2)  # WORD data
    p32(d, setting_off + 16, 0)
    for i, (addr, data) in enumerate(regs):
        p16(d, po + i * 8, addr)
        p16(d, po + i * 8 + 2, data)
        p32(d, po + i * 8 + 4, 0)
    print(f"  res va 0x{setting_off+0x1000:04x} ptr 0x{ptr:04x} n={len(regs)} WORD window")


def patch_imx377(d: bytearray) -> None:
    print(f"  active {u32(d, 0x3688)}x{u32(d, 0x368c)} -> 5344x4016")
    p32(d, 0x3688, 5344)
    p32(d, 0x368C, 4016)
    # mode 0 at VA 0x4C88
    patch_out_info(d, 0x3C88, 5344, 4016, 6024, 4106, "mode0")
    p32(d, 0x3C90, 53100000)
    p32(d, 0x3C94, 42480000)
    # HFR blocks
    patch_out_info(d, 0x3CC0, 5344, 4016, 6024, 4106, "hfr120")
    patch_out_info(d, 0x3CF8, 5344, 4016, 6024, 4106, "hfr240")
    regs = [(0x0340, 4106), (0x0342, 6024), (0x034C, 5344), (0x034E, 4016), (0x0104, 0)]
    for off in (0x3B9C, 0x3BB0, 0x3BC4):
        patch_res_window(d, off, regs)


def patch_ov5693(d: bytearray) -> None:
    print(f"  active {u32(d, 0x3688)}x{u32(d, 0x368c)} -> 2600x1952")
    p32(d, 0x3688, 2600)
    p32(d, 0x368C, 1952)
    # mode 0 at VA 0x4C88
    patch_out_info(d, 0x3C88, 2600, 1952, 2750, 2084, "mode0")
    regs = [(0x0103, 1), (0x0340, 2084), (0x0342, 2750), (0x034C, 2600), (0x034E, 1952)]
    patch_res_window(d, 0x3AD0, regs)
    p32(d, 0x3AD0 + 16, 50)


def main() -> None:
    out = ROOT / "out"
    mag = out / "magisk-talkman-smia" / "system" / "vendor" / "lib"
    jobs = [
        (out / "libmmcamera_imx377.smia2.so", out / "libmmcamera_imx377.smia3.so", patch_imx377),
        (out / "libmmcamera_ov5693.smia2.so", out / "libmmcamera_ov5693.smia3.so", patch_ov5693),
    ]
    for src, dst, fn in jobs:
        d = bytearray(src.read_bytes())
        print(src.name)
        fn(d)
        dst.write_bytes(d)
        (mag / src.name.replace(".smia2.so", ".so")).write_bytes(d)
        print("  wrote", dst)


if __name__ == "__main__":
    main()
