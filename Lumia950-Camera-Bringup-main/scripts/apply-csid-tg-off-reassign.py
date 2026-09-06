#!/usr/bin/env python3
"""After TG-off keep WP 4-lane 0x4320. 2-lane 0x20 was PHY_OVR.
CORE_CTRL_0 = 3 | (0x4320<<4) = 0x43203.
"""

from kernel_tree import kernel_tree, overlay_root
KERNEL_TREE = kernel_tree()
OVERLAY = overlay_root()

from pathlib import Path

CSID = KERNEL_TREE / "drivers/media/platform/msm/camera_v2/sensor/csid/msm_csid.c"


def main() -> None:
    t = CSID.read_text()
    if "0x43203" in t and "WP 4-lane 0x4320" in t:
        print("csid after-off 0x4320 already present")
        return
    for old, label in (
        ("msm_camera_io_w(0x201,", "2-lane 0x20 clk phy1"),
        ("msm_camera_io_w(0x401,", "2-lane 0x40 clk phy1"),
        ("msm_camera_io_w(0x23403,", "0x2340 data permute clk phy1"),
        ("msm_camera_io_w(0x24303,", "0x2430 data permute clk phy1"),
        ("msm_camera_io_w(0x42303,", "0x4230 data swap clk phy1"),
    ):
        if old in t:
            t = t.replace(old, "msm_camera_io_w(0x43203,", 1)
            # replace whichever log string is present
            for s in (
                "after off ctrl0=0x%x (2-lane 0x20 clk phy1)",
                "after off ctrl0=0x%x (2-lane 0x40 clk phy1)",
                "after off ctrl0=0x%x (0x2340 data permute clk phy1)",
                "after off ctrl0=0x%x (0x2430 data permute clk phy1)",
                "after off ctrl0=0x%x (0x4230 data swap clk phy1)",
                "after off ctrl0=0x%x (0x3420 data swap clk phy1)",
            ):
                if s in t:
                    t = t.replace(s, "after off ctrl0=0x%x (WP 4-lane 0x4320)", 1)
                    break
            CSID.write_text(t)
            print("csid: after TG-off CORE_CTRL_0=0x43203 (WP 4-lane)")
            return
    raise SystemExit("after-off CORE_CTRL write not found")


if __name__ == "__main__":
    main()
