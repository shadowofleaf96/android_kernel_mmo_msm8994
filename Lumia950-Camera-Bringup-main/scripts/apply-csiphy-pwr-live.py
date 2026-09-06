#!/usr/bin/env python3
"""#120 live CSI: CSID irq only 0x800 (no PIX SOF). GLBL_PWR_CFG was forced
0 to isolate TG from the PHY. Leave the CAF lane power-up intact.
"""

from kernel_tree import kernel_tree, overlay_root
KERNEL_TREE = kernel_tree()
OVERLAY = overlay_root()

from pathlib import Path

PHY = KERNEL_TREE / "drivers/media/platform/msm/camera_v2/sensor/csiphy/msm_csiphy.c"

OLD = """	msm_camera_io_w(0, csiphybase +
		csiphy_dev->ctrl_reg->csiphy_reg.
		mipi_csiphy_glbl_pwr_cfg_addr);
	pr_err("talkman_csiphy phy off pwr=0x%x\\n",
		msm_camera_io_r(csiphybase +
			csiphy_dev->ctrl_reg->csiphy_reg.
			mipi_csiphy_glbl_pwr_cfg_addr));
"""
NEW = """	pr_err("talkman_csiphy phy left on pwr=0x%x\\n",
		msm_camera_io_r(csiphybase +
			csiphy_dev->ctrl_reg->csiphy_reg.
			mipi_csiphy_glbl_pwr_cfg_addr));
"""


def main() -> None:
    t = PHY.read_text()
    if OLD in t:
        if "talkman_csiphy phy left on pwr=" in t:
            t = t.replace(OLD, "", 1)
            print("csiphy: removed extra GLBL_PWR_CFG=0 (leave-on already logged)")
        else:
            t = t.replace(OLD, NEW, 1)
            print("csiphy: do not force GLBL_PWR_CFG=0")
        PHY.write_text(t)
        return
    if "talkman_csiphy phy left on pwr=" in t:
        print("csiphy GLBL_PWR_CFG leave-on already present")
        return
    raise SystemExit("GLBL_PWR_CFG=0 block not found")


if __name__ == "__main__":
    main()
