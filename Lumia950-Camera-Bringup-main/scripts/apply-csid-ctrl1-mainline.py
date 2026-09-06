#!/usr/bin/env python3
"""#134 CORE_CTRL_1 0x10009 still ECC. Revert to WP 0x1000F."""

from kernel_tree import kernel_tree, overlay_root
KERNEL_TREE = kernel_tree()
OVERLAY = overlay_root()

from pathlib import Path

CSID = KERNEL_TREE / "drivers/media/platform/msm/camera_v2/sensor/csid/msm_csid.c"


def main() -> None:
    t = CSID.read_text()
    if "static int talkman_ctrl1_or = 0x1000F;" in t:
        print("csid ctrl1_or already WP 0x1000F")
        return
    if "static int talkman_ctrl1_or = 0x10009;" not in t:
        raise SystemExit("talkman_ctrl1_or default not found")
    t = t.replace(
        "static int talkman_ctrl1_or = 0x10009;",
        "static int talkman_ctrl1_or = 0x1000F;",
        1,
    )
    CSID.write_text(t)
    print("csid: CORE_CTRL_1 or=0x1000F (revert #134; still ECC)")


if __name__ == "__main__":
    main()
