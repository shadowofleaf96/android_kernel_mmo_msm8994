#!/usr/bin/env python3
"""#149: restore CSID TG 4080x3028.

#145 2496x1872 TG ECC's while enabled (0x2000200). Daily pink is 4080
incrementing. Keep CAMIF 2496 and WP LUT for after TG-off. One change.
"""

from kernel_tree import kernel_tree, overlay_root
KERNEL_TREE = kernel_tree()
OVERLAY = overlay_root()

from pathlib import Path

CSID = KERNEL_TREE / "drivers/media/platform/msm/camera_v2/sensor/csid/msm_csid.c"


def main() -> None:
    t = CSID.read_text()
    if "static int talkman_tg_w = 4080;" in t and "static int talkman_tg_h = 3028;" in t:
        print("csid TG 4080x3028 already present")
        return
    old_w = "static int talkman_tg_w = 2496;"
    old_h = "static int talkman_tg_h = 1872;"
    if old_w not in t or old_h not in t:
        raise SystemExit("csid talkman_tg_w/h 2496x1872 not found")
    t = t.replace(old_w, "static int talkman_tg_w = 4080;", 1)
    t = t.replace(old_h, "static int talkman_tg_h = 3028;", 1)
    CSID.write_text(t)
    print("csid: TG 2496x1872 -> 4080x3028 (known-good generator)")


if __name__ == "__main__":
    main()
