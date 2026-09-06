#!/usr/bin/env python3
"""Find cpp_hardware_process_streamon and dump nearby ARM32 instructions."""
from pathlib import Path
import struct
import sys

if len(sys.argv) < 2:
    sys.exit("usage: disasm-cpp-streamon.py <libmmcamera2_cpp_module.so>")
so = Path(sys.argv[1])
data = so.read_bytes()
needle = b"cpp_hardware_process_streamon"
idx = data.find(needle)
print("string at", hex(idx), "file_size", len(data))

# ELF32
assert data[:4] == b"\x7fELF"
e_type, e_machine = struct.unpack_from("<HH", data, 16)
e_entry, e_phoff, e_shoff = struct.unpack_from("<III", data, 24)
e_ehsize, e_phentsize, e_phnum = struct.unpack_from("<HHH", data, 40)
print("machine", hex(e_machine), "phoff", e_phoff, "phnum", e_phnum)

loads = []
for i in range(e_phnum):
    off = e_phoff + i * e_phentsize
    p_type, p_offset, p_vaddr, p_paddr, p_filesz, p_memsz, p_flags, p_align = \
        struct.unpack_from("<IIIIIIII", data, off)
    if p_type == 1:
        loads.append((p_offset, p_vaddr, p_filesz, p_flags))
        print(f"LOAD off={p_offset:#x} va={p_vaddr:#x} filesz={p_filesz:#x} flags={p_flags:#x}")


def file_to_va(foff):
    for p_offset, p_vaddr, p_filesz, p_flags in loads:
        if p_offset <= foff < p_offset + p_filesz:
            return p_vaddr + (foff - p_offset)
    return None


str_va = file_to_va(idx)
print("string VA", hex(str_va) if str_va else None)

# Search for ARM LDR literal / add-pc that materializes str_va.
# Also search for the 32-bit value str_va in .text (absolute address in literal pool).
hits = []
if str_va is not None:
    pat = struct.pack("<I", str_va)
    start = 0
    while True:
        h = data.find(pat, start)
        if h < 0:
            break
        hits.append(h)
        start = h + 1
print("literal-pool hits", [hex(h) for h in hits[:20]], "count", len(hits))

# Find BL to ioctl: look around functions that reference the error string
err = b"error: v4l2 ioctl() failed"
err_i = data.find(err)
print("err string", hex(err_i), "VA", hex(file_to_va(err_i) or 0))
err_va = file_to_va(err_i)
err_hits = []
if err_va:
    pat = struct.pack("<I", err_va)
    start = 0
    while True:
        h = data.find(pat, start)
        if h < 0:
            break
        err_hits.append(h)
        start = h + 1
print("err literal hits", [hex(h) for h in err_hits[:20]])

try:
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
    md = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    md.detail = False
    have = True
except Exception as e:
    print("capstone", e)
    have = False

# Disassemble 256 bytes before each err literal (function body)
text_off = loads[0][0]
text_va = loads[0][1]
text_sz = loads[0][2]
text = data[text_off:text_off + text_sz]


def va_to_file(va):
    for p_offset, p_vaddr, p_filesz, p_flags in loads:
        if p_vaddr <= va < p_vaddr + p_filesz:
            return p_offset + (va - p_vaddr)
    return None


if have:
    for h in err_hits[:5]:
        va = file_to_va(h)
        print("\n=== around err literal", hex(h), "va", hex(va or 0), "===")
        # literal is in .text; scan 0x400 bytes before
        foff = max(0, h - 0x200)
        blob = data[foff:h + 16]
        for insn in md.disasm(blob, text_va + (foff - text_off) if foff >= text_off else 0):
            m = f"{insn.address:08x}: {insn.mnemonic:8} {insn.op_str}"
            if insn.address >= (va or 0) - 0x80:
                print(m)

# Also print relocs to ioctl
dynstr_i = data.find(b"ioctl\0")
print("\nioctl str", hex(dynstr_i) if dynstr_i >= 0 else None)
