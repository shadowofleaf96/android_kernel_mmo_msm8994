#!/usr/bin/env python3
"""#141: WP live CFG3 (+0x08) is 0x16. Linux writes settle 0x23 there.
"""

from kernel_tree import kernel_tree, overlay_root
KERNEL_TREE = kernel_tree()
OVERLAY = overlay_root()

from pathlib import Path

PHY = KERNEL_TREE / "drivers/media/platform/msm/camera_v2/sensor/csiphy/msm_csiphy.c"

OLD = """		msm_camera_io_w(csiphy_params->settle_cnt,
			csiphybase + csiphy_dev->ctrl_reg->csiphy_reg.
			mipi_csiphy_lnn_cfg3_addr + 0x40*j);
"""

NEW = """		msm_camera_io_w(csiphy_params->settle_cnt,
			csiphybase + csiphy_dev->ctrl_reg->csiphy_reg.
			mipi_csiphy_lnn_cfg3_addr + 0x40*j);
		/* WP live Hill CFG3=0x16 (Linux settle 0x23). */
		msm_camera_io_w(0x16, csiphybase +
			csiphy_dev->ctrl_reg->csiphy_reg.
			mipi_csiphy_lnn_cfg3_addr + 0x40*j);
		pr_err("talkman_csiphy wp cfg3 j=%d settle=0x%x now=0x%x\\n",
			j, csiphy_params->settle_cnt,
			msm_camera_io_r(csiphybase +
			csiphy_dev->ctrl_reg->csiphy_reg.
			mipi_csiphy_lnn_cfg3_addr + 0x40*j));
"""


def main() -> None:
    t = PHY.read_text()
    if "talkman_csiphy wp cfg3 j=" in t:
        print("csiphy WP CFG3=0x16 already present")
        return
    if OLD not in t:
        raise SystemExit("CFG3 settle write not found")
    PHY.write_text(t.replace(OLD, NEW, 1))
    print("csiphy: WP CFG3=0x16 (was settle 0x23)")


if __name__ == "__main__":
    main()
