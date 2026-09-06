#!/usr/bin/env python3
"""#139: match live WP CSIPHY0 analog (KD 2026-08-22).

Linux Open Camera left idle pads: CFG4=0x5 CFG5=0x52. WP Camera preview
on CSIPHY0 is CFG4=0xff CFG5=0x22, test_imp=0x17, pwr=0x3f.
Keep test_imp 0x17. Do not stack 2-lane / CFG4=0 / CFG5=0.
"""

from kernel_tree import kernel_tree, overlay_root
KERNEL_TREE = kernel_tree()
OVERLAY = overlay_root()

from pathlib import Path

PHY = KERNEL_TREE / "drivers/media/platform/msm/camera_v2/sensor/csiphy/msm_csiphy.c"

OLD = """			if (talkman_cfg4_clr0) {
				uint32_t c4 = msm_camera_io_r(csiphybase +
					csiphy_dev->ctrl_reg->csiphy_reg.
					mipi_csiphy_lnn_cfg4_addr + 0x40*j);

				msm_camera_io_w(0, csiphybase +
					csiphy_dev->ctrl_reg->csiphy_reg.
					mipi_csiphy_lnn_cfg4_addr + 0x40*j);
			}
			curr_lane++;
"""

NEW = """			if (talkman_cfg4_clr0) {
				uint32_t c4 = msm_camera_io_r(csiphybase +
					csiphy_dev->ctrl_reg->csiphy_reg.
					mipi_csiphy_lnn_cfg4_addr + 0x40*j);

				msm_camera_io_w(0, csiphybase +
					csiphy_dev->ctrl_reg->csiphy_reg.
					mipi_csiphy_lnn_cfg4_addr + 0x40*j);
			}
			{
				uint32_t c4 = msm_camera_io_r(csiphybase +
					csiphy_dev->ctrl_reg->csiphy_reg.
					mipi_csiphy_lnn_cfg4_addr + 0x40*j);
				uint32_t c5 = msm_camera_io_r(csiphybase +
					csiphy_dev->ctrl_reg->csiphy_reg.
					mipi_csiphy_lnn_cfg5_addr + 0x40*j);

				/* WP live Hill: CFG4=0xff CFG5=0x22. */
				msm_camera_io_w(0xff, csiphybase +
					csiphy_dev->ctrl_reg->csiphy_reg.
					mipi_csiphy_lnn_cfg4_addr + 0x40*j);
				msm_camera_io_w(0x22, csiphybase +
					csiphy_dev->ctrl_reg->csiphy_reg.
					mipi_csiphy_lnn_cfg5_addr + 0x40*j);
				pr_err("talkman_csiphy wp analog j=%d cfg4 was=0x%x now=0x%x cfg5 was=0x%x now=0x%x\\n",
					j, c4, msm_camera_io_r(csiphybase +
					csiphy_dev->ctrl_reg->csiphy_reg.
					mipi_csiphy_lnn_cfg4_addr + 0x40*j),
					c5, msm_camera_io_r(csiphybase +
					csiphy_dev->ctrl_reg->csiphy_reg.
					mipi_csiphy_lnn_cfg5_addr + 0x40*j));
			}
			curr_lane++;
"""


def main() -> None:
    t = PHY.read_text()
    if "talkman_csiphy wp analog j=" in t:
        print("csiphy WP analog CFG4=0xff CFG5=0x22 already present")
        return
    if OLD not in t:
        raise SystemExit("cfg4_clr0 block not found for WP analog")
    PHY.write_text(t.replace(OLD, NEW, 1))
    print("csiphy: WP analog CFG4=0xff CFG5=0x22")


if __name__ == "__main__":
    main()
