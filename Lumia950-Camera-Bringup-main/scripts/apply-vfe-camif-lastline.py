#!/usr/bin/env python3
"""#97: epoch0=3027 fires, next SOF 1 ms later, no CAMIF EOF.

CAMIF window last_line is inclusive and currently equals the last TG
line (3027). EOF is supposed to fire after the window, on FE/V-blank.
Pull last_line back one so line 3027 (and epoch) sit past the window.
Keep lpf=3028 / epoch0=3027.
"""

from kernel_tree import kernel_tree, overlay_root
KERNEL_TREE = kernel_tree()
OVERLAY = overlay_root()

from pathlib import Path

VFE = KERNEL_TREE / "drivers/media/platform/msm/camera_v2/isp/msm_isp44.c"

OLD = "		last_line = talkman_lpf ? talkman_lpf - 1 : 0;"
NEW = "		last_line = talkman_lpf > 1 ? talkman_lpf - 2 : 0;"


def main() -> None:
    t = VFE.read_text()
    if "talkman_vfe camif ff0b" in t:
        print("vfe camif last_line skipped (ff0b uses lpf-1)")
        return
    if "talkman_lpf > 1 ? talkman_lpf - 2" in t:
        print("vfe camif last_line lpf-2 already present")
        return
    if OLD not in t:
        raise SystemExit("vfe44 fullwin last_line assign not found")
    t = t.replace(OLD, NEW, 1)
    VFE.write_text(t)
    print("vfe44: last_line = lpf-2 (3026)")


if __name__ == "__main__":
    main()
