#!/usr/bin/env python3
"""#96: epoch0=3027 fires every frame ~26 ms after SOF, then next SOF in
~0.5 ms with no CAMIF EOF. CAMIF counts all 3028 lines; FE/V-blank is
too short for EOF. CAF TG_VC V blank is bits 31:24 (max 0xFF). We used
0x80=128. Bump to 0xFF.
"""

from kernel_tree import kernel_tree, overlay_root
KERNEL_TREE = kernel_tree()
OVERLAY = overlay_root()

from pathlib import Path

CSID = KERNEL_TREE / "drivers/media/platform/msm/camera_v2/sensor/csid/msm_csid.c"


def main() -> None:
    t = CSID.read_text()
    old = "		tgv = ((0x80 & 0xFF) << 24) | ((0x400 & 0x7FF) << 13);"
    new = "		tgv = ((0xFF & 0xFF) << 24) | ((0x400 & 0x7FF) << 13);"
    if "((0xFF & 0xFF) << 24) | ((0x400" in t:
        print("csid TG V-blank 0xFF already present")
        return
    if old not in t:
        raise SystemExit("csid TG_VC V-blank 0x80 write not found")
    t = t.replace(old, new, 1)
    CSID.write_text(t)
    print("csid: TG V-blank 0x80 -> 0xFF")


if __name__ == "__main__":
    main()
