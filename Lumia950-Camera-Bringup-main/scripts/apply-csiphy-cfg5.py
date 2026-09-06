#!/usr/bin/env python3
"""Undo #132 CFG5=0. 20nm default 0x52 still ECC; do not stack with CORE_CTRL_1.
"""

from kernel_tree import kernel_tree, overlay_root
KERNEL_TREE = kernel_tree()
OVERLAY = overlay_root()

from pathlib import Path

PHY = KERNEL_TREE / "drivers/media/platform/msm/camera_v2/sensor/csiphy/msm_csiphy.c"

BLOCK = """			{
				uint32_t c5 = msm_camera_io_r(csiphybase +
					csiphy_dev->ctrl_reg->csiphy_reg.
					mipi_csiphy_lnn_cfg5_addr + 0x40*j);

				msm_camera_io_w(0, csiphybase +
					csiphy_dev->ctrl_reg->csiphy_reg.
					mipi_csiphy_lnn_cfg5_addr + 0x40*j);
				pr_err("talkman_csiphy cfg5 j=%d was=0x%x now=0x%x\\n",
					j, c5, msm_camera_io_r(csiphybase +
					csiphy_dev->ctrl_reg->csiphy_reg.
					mipi_csiphy_lnn_cfg5_addr + 0x40*j));
			}
"""


def main() -> None:
    t = PHY.read_text()
    if "talkman_csiphy cfg5 j=" not in t:
        print("csiphy CFG5 force already removed")
        return
    if BLOCK not in t:
        raise SystemExit("CFG5 force block not found to remove")
    PHY.write_text(t.replace(BLOCK, "", 1))
    print("csiphy: removed CFG5 force 0")


if __name__ == "__main__":
    main()
