#!/usr/bin/env python3
"""Remove 2-lane CSIPHY force. 2-lane irq is PHY_OVR (CSID 3.0 0x00F00000),
not a scene path. Back to HAL/DT 4-lane mask 0x1f.
"""

from kernel_tree import kernel_tree, overlay_root
KERNEL_TREE = kernel_tree()
OVERLAY = overlay_root()

from pathlib import Path

CSIPHY = KERNEL_TREE / "drivers/media/platform/msm/camera_v2/sensor/csiphy/msm_csiphy.c"

FORCE = """
	csiphy_params->lane_cnt = 2;
	csiphy_params->lane_mask = 0x7;
	pr_err("talkman_csiphy 2-lane force mask=0x7\\n");
"""
FORCE13 = """
	csiphy_params->lane_cnt = 2;
	csiphy_params->lane_mask = 0x13;
	pr_err("talkman_csiphy 2-lane force mask=0x13\\n");
"""


def main() -> None:
    t = CSIPHY.read_text()
    if "2-lane force mask=" not in t:
        print("csiphy 2-lane force already removed")
        return
    if FORCE in t:
        CSIPHY.write_text(t.replace(FORCE, "\n", 1))
        print("csiphy: removed 2-lane mask 0x7 force")
        return
    if FORCE13 in t:
        CSIPHY.write_text(t.replace(FORCE13, "\n", 1))
        print("csiphy: removed 2-lane mask 0x13 force")
        return
    raise SystemExit("2-lane force block not found")


if __name__ == "__main__":
    main()
