#!/usr/bin/env python3
"""Parse a 32-bit ARM libmmcamera_*.so and dump sensor_lib pointers / I2C arrays."""
from __future__ import annotations

import struct
import sys
from pathlib import Path


def u16(d: bytes, o: int) -> int:
    return struct.unpack_from("<H", d, o)[0]


def u32(d: bytes, o: int) -> int:
    return struct.unpack_from("<I", d, o)[0]


def load(path: Path) -> bytes:
    return path.read_bytes()


def va_to_off(va: int) -> int | None:
    # This .so is ET_DYN with typical Android layout:
    # .text/.rodata file==va, .data va 0x4000 file 0x3000 (va-0x1000)
    if 0x4000 <= va < 0x7000:
        return va - 0x1000
    if 0x134 <= va < 0x3e44:
        return va
    if 0x3e44 <= va < 0x4000:
        return va - 0x1000
    return None


def looks_ptr(va: int) -> bool:
    return 0x2000 <= va < 0x7000


def dump_reg_array(d: bytes, va: int, n: int, stride: int) -> None:
    off = va_to_off(va)
    if off is None:
        print(f"    cannot map va 0x{va:x}")
        return
    for i in range(min(n, 12)):
        o = off + i * stride
        if stride == 8:
            addr, data, delay = u16(d, o), u16(d, o + 2), u32(d, o + 4)
            print(f"    [{i:3d}] 0x{addr:04x} = 0x{data:04x} delay={delay}")
        else:
            addr, data = u16(d, o), u16(d, o + 2)
            print(f"    [{i:3d}] 0x{addr:04x} = 0x{data:04x}")
    if n > 12:
        print(f"    ... {n} entries")


def scan_i2c_arrays(d: bytes) -> None:
    """Find runs of (u16 addr in 0x0000-0x4000, u16 data, u32 delay==0/small)."""
    data_off, data_len = 0x3000, 0x2230
    print("\n=== candidate 8-byte I2C arrays in .data ===")
    i = data_off
    end = data_off + data_len - 8
    while i <= end:
        addr = u16(d, i)
        data = u16(d, i + 2)
        delay = u32(d, i + 4)
        if addr < 0x4000 and delay <= 200 and (data <= 0xFF or data <= 0xFFFF):
            run = 0
            j = i
            while j <= end:
                a = u16(d, j)
                dl = u32(d, j + 4)
                if a > 0x4000 or dl > 200:
                    break
                run += 1
                j += 8
            if run >= 8:
                print(
                    f"  file 0x{i:04x} va 0x{i+0x1000:04x} run={run} "
                    f"first=0x{addr:04x}=0x{data:04x}"
                )
                i = j
                continue
        i += 2


def main() -> None:
    path = Path(sys.argv[1])
    d = load(path)
    print(f"file {path} size {len(d)}")
    print("sensor_open_lib bytes:", d[0x939:0x945].hex())

    # ARM: often  ldr r0, [pc, #imm]; bx lr
    # Thumb: same at odd addr. Function value 0x939 is thumb.
    thumb = d[0x938:0x944]
    print("aligned 0x938:", thumb.hex())
    # Thumb ldr r0, [pc, #imm]: 48 xx
    if thumb[0] == 0x48 or thumb[1] == 0x48:
        print("thumb ldr r0 pattern")

    print("\n=== strings near .data start ===")
    for off in range(0x3000, 0x3100, 16):
        chunk = d[off : off + 16]
        print(f"{off:04x} {chunk.hex()} {chunk!r}")

    print("\n=== slave_info region (file 0x30A8 / va 0x40A8) ===")
    for off in range(0x3080, 0x3180, 16):
        print(f"{off:04x} {d[off:off+16].hex()}")

    print("\n=== .data.rel.ro ===")
    for off in range(0x2E48, 0x2E90, 4):
        v = u32(d, off)
        print(f"  file 0x{off:04x} -> 0x{v:08x}")

    print("\n=== rel.dyn pointer targets in .data ===")
    # parse ELF rel.dyn: offset 0x4d4, 0x258 bytes, 8-byte REL
    rel_off, rel_size = 0x4D4, 0x258
    ptrs = []
    for i in range(0, rel_size, 8):
        r_offset = u32(d, rel_off + i)
        r_info = u32(d, rel_off + i + 4)
        file_off = va_to_off(r_offset)
        val = u32(d, file_off) if file_off is not None and file_off + 4 <= len(d) else None
        if val is not None and looks_ptr(val):
            ptrs.append((r_offset, val))
    print(f"{len(ptrs)} relocated pointers into image")
    for r_offset, val in ptrs:
        print(f"  *0x{r_offset:04x} = 0x{val:04x}")

    scan_i2c_arrays(d)

    # dump likely sensor_lib_ptr: search for pointer to "imx377" / "ov5693"
    for name in (b"imx377\x00", b"ov5693\x00", b"m24c64s\x00"):
        idx = d.find(name)
        print(f"\nstring {name!r} file={idx} va={idx+0x1000 if idx>=0x3000 else idx}")


if __name__ == "__main__":
    main()
