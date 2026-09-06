#!/usr/bin/env python3
"""Rewrite IMX377/OV5693 sensor-lib I2C arrays to SMIA++ reset/stream/hold.

Probe already matches Sharp 0xEACA / 0x2140. Session init still writes Sony/OV
maps and NACKs. Keep chromatix names; drop EEPROM/actuator/flash so missing
subdevs do not block capability query.
"""
from __future__ import annotations

import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def u16(d: bytearray, o: int) -> int:
    return struct.unpack_from("<H", d, o)[0]


def u32(d: bytearray, o: int) -> int:
    return struct.unpack_from("<I", d, o)[0]


def p16(d: bytearray, o: int, v: int) -> None:
    struct.pack_into("<H", d, o, v)


def p32(d: bytearray, o: int, v: int) -> None:
    struct.pack_into("<I", d, o, v)


def va2off(va: int) -> int | None:
    if 0x4000 <= va < 0x7000:
        return va - 0x1000
    return None


def clear_name(d: bytearray, file_off: int, label: str) -> None:
    old = bytes(d[file_off : file_off + 32]).split(b"\x00", 1)[0]
    d[file_off : file_off + 32] = b"\x00" * 32
    print(f"  clear {label} {old!r}")


def write_reg(d: bytearray, arr_off: int, addr: int, data: int, delay: int = 0) -> None:
    p16(d, arr_off, addr)
    p16(d, arr_off + 2, data)
    p32(d, arr_off + 4, delay)


def patch_settings(d: bytearray, name: str) -> int:
    n = 0
    for o in range(0x3000, min(len(d) - 20, 0x5230), 4):
        ptr = u32(d, o)
        size = u32(d, o + 4)
        at = u32(d, o + 8)
        dt = u32(d, o + 12)
        delay = u32(d, o + 16)
        po = va2off(ptr)
        if po is None or not (1 <= size <= 400 and at == 2 and dt == 1 and delay <= 200):
            continue
        a0, d0 = u16(d, po), u16(d, po + 2)
        # Already-safe SMIA 8-bit controls: keep, but shrink long init to reset only.
        if a0 == 0x0103 and size > 1:
            p32(d, o + 4, 1)
            p32(d, o + 16, 50)
            print(f"  {name} va 0x{o+0x1000:04x} init {size} -> SMIA reset 0x0103")
            n += 1
            continue
        if a0 in (0x0100, 0x0103, 0x0104) and size == 1:
            continue

        if a0 == 0x3018 and d0 == 0x00A2:
            addr, data, new_delay, why = 0x0100, 0x0001, 0, "start"
        elif a0 == 0x3018 and d0 == 0x00A3:
            addr, data, new_delay, why = 0x0100, 0x0000, 0, "stop"
        elif a0 == 0x302D and d0 == 0x0001:
            addr, data, new_delay, why = 0x0104, 0x0001, 0, "groupon"
        elif a0 == 0x302D and d0 == 0x0000:
            addr, data, new_delay, why = 0x0104, 0x0000, 0, "groupoff"
        elif a0 == 0x3208:
            addr, data, new_delay, why = 0x0104, (0x0001 if d0 == 0 else 0x0000), 0, "ov-group"
        elif size >= 20:
            addr, data, new_delay, why = 0x0103, 0x0001, 50, "init-reset"
        else:
            addr, data, new_delay, why = 0x0104, 0x0000, 0, "nop-hold"

        write_reg(d, po, addr, data, 0)
        p32(d, o + 4, 1)
        p32(d, o + 16, new_delay)
        print(
            f"  {name} va 0x{o+0x1000:04x} {why}: "
            f"0x{a0:04x}=0x{d0:04x} n={size} -> 0x{addr:04x}=0x{data:04x}"
        )
        n += 1
    return n


def patch_one(src: Path, dst: Path) -> None:
    d = bytearray(src.read_bytes())
    print(f"patch {src.name} -> {dst.name}")
    # sensor_lib_t / slave_info names at VA 0x4008
    clear_name(d, 0x3028, "eeprom")
    clear_name(d, 0x3048, "actuator")
    clear_name(d, 0x3068, "ois")
    clear_name(d, 0x3088, "flash")
    n = patch_settings(d, src.stem)
    dst.write_bytes(d)
    print(f"  wrote {dst} ({n} settings)")


def main() -> None:
    out = ROOT / "out"
    mag = out / "magisk-talkman-smia" / "system" / "vendor" / "lib"
    mag.mkdir(parents=True, exist_ok=True)
    pairs = [
        (out / "libmmcamera_imx377.smia.so", out / "libmmcamera_imx377.smia2.so"),
        (out / "libmmcamera_ov5693.smia.so", out / "libmmcamera_ov5693.smia2.so"),
    ]
    for src, dst in pairs:
        if not src.exists():
            raise SystemExit(f"missing {src}")
        patch_one(src, dst)
        (mag / src.name.replace(".smia.so", ".so")).write_bytes(dst.read_bytes())
    print("copied into Magisk module")


if __name__ == "__main__":
    main()
