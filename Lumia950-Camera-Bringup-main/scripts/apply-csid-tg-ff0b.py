#!/usr/bin/env python3
"""#145: size CSID TG to WP VF 2496x1872 so it matches #144 CAMIF.

#144 overflowed 0xff8 because TG stayed 4080x3028. That is the green
lines in the pink ramp, not CSI decode. Do not change pixclk, CAMIF
regs, or TG-off in this flash.
"""

from kernel_tree import kernel_tree, overlay_root
KERNEL_TREE = kernel_tree()
OVERLAY = overlay_root()

from pathlib import Path

CSID = KERNEL_TREE / "drivers/media/platform/msm/camera_v2/sensor/csid/msm_csid.c"


def main() -> None:
    t = CSID.read_text()
    if "static int talkman_tg_w = 2496;" in t and "static int talkman_tg_h = 1872;" in t:
        print("csid TG 2496x1872 already present")
        return
    old_w = "static int talkman_tg_w = 4080;"
    old_h = "static int talkman_tg_h = 3028;"
    if old_w not in t or old_h not in t:
        raise SystemExit("csid talkman_tg_w/h 4080x3028 not found")
    t = t.replace(old_w, "static int talkman_tg_w = 2496;", 1)
    t = t.replace(old_h, "static int talkman_tg_h = 1872;", 1)
    CSID.write_text(t)
    print("csid: TG 4080x3028 -> WP VF 2496x1872")


if __name__ == "__main__":
    main()
