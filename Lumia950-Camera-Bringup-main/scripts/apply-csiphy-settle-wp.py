#!/usr/bin/env python3
"""WP SMIApp settle for Hill DDRClk 53.1 MHz @ 200 MHz PHYTIMER is ~0x23.
Linux force was 0x28 (#50 still ECC). Try the WP value now that 0x0100=1.
"""

from kernel_tree import kernel_tree, overlay_root
KERNEL_TREE = kernel_tree()
OVERLAY = overlay_root()

from pathlib import Path

PHY = KERNEL_TREE / "drivers/media/platform/msm/camera_v2/sensor/csiphy/msm_csiphy.c"


def main() -> None:
    t = PHY.read_text()
    if "static int talkman_settle = 0x23;" in t:
        print("csiphy settle already WP 0x23")
        return
    if "static int talkman_settle = 0x28;" not in t:
        raise SystemExit("talkman_settle default not found")
    t = t.replace(
        "static int talkman_settle = 0x28;",
        "static int talkman_settle = 0x23;",
        1,
    )
    PHY.write_text(t)
    print("csiphy: settle 0x23 (WP Hill 53.1 MHz)")


if __name__ == "__main__":
    main()
