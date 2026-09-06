#!/usr/bin/env python3
"""Undo #133 test_imp 0x10. Restore 20nm 0x17.
"""

from kernel_tree import kernel_tree, overlay_root
KERNEL_TREE = kernel_tree()
OVERLAY = overlay_root()

from pathlib import Path

PHY = KERNEL_TREE / "drivers/media/platform/msm/camera_v2/sensor/csiphy/msm_csiphy.c"

OLD = """			msm_camera_io_w(0x10, csiphybase +
				csiphy_dev->ctrl_reg->csiphy_reg.
				mipi_csiphy_lnn_test_imp + 0x40*j);
			pr_err("talkman_csiphy test_imp=0x10 j=%d\\n", j);
"""
NEW = """			msm_camera_io_w(0x17, csiphybase +
				csiphy_dev->ctrl_reg->csiphy_reg.
				mipi_csiphy_lnn_test_imp + 0x40*j);
"""


def main() -> None:
    t = PHY.read_text()
    if "talkman_csiphy test_imp=0x10" not in t:
        print("csiphy test_imp already 0x17")
        return
    if OLD not in t:
        raise SystemExit("test_imp 0x10 block not found to revert")
    PHY.write_text(t.replace(OLD, NEW, 1))
    print("csiphy: test_imp 0x10 -> 0x17")


if __name__ == "__main__":
    main()
