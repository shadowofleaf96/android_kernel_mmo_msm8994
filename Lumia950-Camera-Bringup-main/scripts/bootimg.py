#!/usr/bin/env python3
"""Replace the kernel in an Android boot v0 image. Ramdisk is copied as-is
(so an already-patched Magisk ramdisk stays patched if you use Magisk).

Usage:
  bootimg.py info <boot.img>
  bootimg.py replace-kernel <boot.img> <Image.gz-dtb> <output.img>
"""

import struct
import sys

BOOT_MAGIC = b"ANDROID!"
HEADER_FMT = "<8sIIIIIIIIII16s512s32s1024s"
HEADER_SIZE = struct.calcsize(HEADER_FMT)


class BootImage:
    def __init__(self, data):
        if not data.startswith(BOOT_MAGIC):
            raise ValueError("not an Android boot image")
        (
            _magic,
            self.kernel_size,
            self.kernel_addr,
            self.ramdisk_size,
            self.ramdisk_addr,
            self.second_size,
            self.second_addr,
            self.tags_addr,
            self.page_size,
            self.header_version,
            self.os_version,
            self.name,
            self.cmdline,
            self.id,
            self.extra_cmdline,
        ) = struct.unpack(HEADER_FMT, data[:HEADER_SIZE])
        if self.header_version != 0:
            raise ValueError("unsupported boot header version %d" %
                             self.header_version)
        offset = self._pages(HEADER_SIZE)
        self.kernel = data[offset:offset + self.kernel_size]
        offset += self._pages(self.kernel_size)
        self.ramdisk = data[offset:offset + self.ramdisk_size]
        offset += self._pages(self.ramdisk_size)
        self.second = data[offset:offset + self.second_size]

    def _pages(self, size):
        return (size + self.page_size - 1) // self.page_size * self.page_size

    def _pad(self, blob):
        return blob + b"\0" * (self._pages(len(blob)) - len(blob))

    def pack(self):
        header = struct.pack(
            HEADER_FMT,
            BOOT_MAGIC,
            len(self.kernel), self.kernel_addr,
            len(self.ramdisk), self.ramdisk_addr,
            len(self.second), self.second_addr,
            self.tags_addr,
            self.page_size,
            self.header_version,
            self.os_version,
            self.name,
            self.cmdline,
            self.id,
            self.extra_cmdline,
        )
        return (self._pad(header) + self._pad(self.kernel) +
                self._pad(self.ramdisk) + self._pad(self.second))

    def describe(self):
        cmdline = self.cmdline.rstrip(b"\0").decode("utf-8", "replace")
        return "\n".join([
            "page size: %d" % self.page_size,
            "kernel: %d bytes @ 0x%08x" % (self.kernel_size, self.kernel_addr),
            "ramdisk: %d bytes @ 0x%08x" % (self.ramdisk_size, self.ramdisk_addr),
            "second: %d bytes" % self.second_size,
            "cmdline: %s" % cmdline,
        ])


def main(argv):
    if len(argv) < 3:
        print(__doc__, file=sys.stderr)
        return 2
    command = argv[1]
    if command == "info":
        with open(argv[2], "rb") as f:
            print(BootImage(f.read()).describe())
        return 0
    if command == "replace-kernel":
        if len(argv) != 5:
            print(__doc__, file=sys.stderr)
            return 2
        with open(argv[2], "rb") as f:
            image = BootImage(f.read())
        with open(argv[3], "rb") as f:
            image.kernel = f.read()
        with open(argv[4], "wb") as f:
            f.write(image.pack())
        print("wrote %s (kernel %d bytes, ramdisk %d bytes preserved)" %
              (argv[4], len(image.kernel), len(image.ramdisk)))
        return 0
    print("unknown command: %s" % command, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
