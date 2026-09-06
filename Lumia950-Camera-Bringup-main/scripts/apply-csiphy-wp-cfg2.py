#!/usr/bin/env python3
"""#140: WP live CSIPHY0 CFG2 (+0x04) is 0x3f. Linux 20nm writes 0x10.
Keep #139 CFG4=0xff CFG5=0x22. Also dump +0x2c (WP 0x70).
"""

from kernel_tree import kernel_tree, overlay_root
KERNEL_TREE = kernel_tree()
OVERLAY = overlay_root()

from pathlib import Path

PHY = KERNEL_TREE / "drivers/media/platform/msm/camera_v2/sensor/csiphy/msm_csiphy.c"

OLD = """				pr_err("talkman_csiphy wp analog j=%d cfg4 was=0x%x now=0x%x cfg5 was=0x%x now=0x%x\\n",
					j, c4, msm_camera_io_r(csiphybase +
					csiphy_dev->ctrl_reg->csiphy_reg.
					mipi_csiphy_lnn_cfg4_addr + 0x40*j),
					c5, msm_camera_io_r(csiphybase +
					csiphy_dev->ctrl_reg->csiphy_reg.
					mipi_csiphy_lnn_cfg5_addr + 0x40*j));
"""

NEW = """				{
					uint32_t c2 = msm_camera_io_r(
						csiphybase +
						csiphy_dev->ctrl_reg->
						csiphy_reg.
						mipi_csiphy_lnn_cfg2_addr +
						0x40*j);

					msm_camera_io_w(0x3f, csiphybase +
						csiphy_dev->ctrl_reg->
						csiphy_reg.
						mipi_csiphy_lnn_cfg2_addr +
						0x40*j);
					pr_err("talkman_csiphy wp cfg2 j=%d was=0x%x now=0x%x\\n",
						j, c2, msm_camera_io_r(
						csiphybase +
						csiphy_dev->ctrl_reg->
						csiphy_reg.
						mipi_csiphy_lnn_cfg2_addr +
						0x40*j));
				}
				pr_err("talkman_csiphy wp analog j=%d cfg4 was=0x%x now=0x%x cfg5 was=0x%x now=0x%x\\n",
					j, c4, msm_camera_io_r(csiphybase +
					csiphy_dev->ctrl_reg->csiphy_reg.
					mipi_csiphy_lnn_cfg4_addr + 0x40*j),
					c5, msm_camera_io_r(csiphybase +
					csiphy_dev->ctrl_reg->csiphy_reg.
					mipi_csiphy_lnn_cfg5_addr + 0x40*j));
"""

DUMP_OLD = """		pr_err("talkman_csiphy dump j=%d 00=0x%x 04=0x%x 08=0x%x 0c=0x%x 10=0x%x 14=0x%x 18=0x%x 1c=0x%x 20=0x%x 28=0x%x\\n",
			j,
			msm_camera_io_r(ln + 0x00),
			msm_camera_io_r(ln + 0x04),
			msm_camera_io_r(ln + 0x08),
			msm_camera_io_r(ln + 0x0c),
			msm_camera_io_r(ln + 0x10),
			msm_camera_io_r(ln + 0x14),
			msm_camera_io_r(ln + 0x18),
			msm_camera_io_r(ln + 0x1c),
			msm_camera_io_r(ln + 0x20),
			msm_camera_io_r(ln + 0x28));
"""

DUMP_NEW = """		pr_err("talkman_csiphy dump j=%d 00=0x%x 04=0x%x 08=0x%x 0c=0x%x 10=0x%x 14=0x%x 18=0x%x 1c=0x%x 20=0x%x 28=0x%x 2c=0x%x\\n",
			j,
			msm_camera_io_r(ln + 0x00),
			msm_camera_io_r(ln + 0x04),
			msm_camera_io_r(ln + 0x08),
			msm_camera_io_r(ln + 0x0c),
			msm_camera_io_r(ln + 0x10),
			msm_camera_io_r(ln + 0x14),
			msm_camera_io_r(ln + 0x18),
			msm_camera_io_r(ln + 0x1c),
			msm_camera_io_r(ln + 0x20),
			msm_camera_io_r(ln + 0x28),
			msm_camera_io_r(ln + 0x2c));
"""


def main() -> None:
    t = PHY.read_text()
    if "talkman_csiphy wp cfg2 j=" in t:
        print("csiphy WP CFG2=0x3f already present")
    elif OLD not in t:
        raise SystemExit("WP analog log not found for CFG2")
    else:
        t = t.replace(OLD, NEW, 1)
        print("csiphy: WP CFG2=0x3f (was 0x10)")

    if "28=0x%x 2c=0x%x" in t:
        print("csiphy dump +0x2c already present")
    elif DUMP_OLD not in t:
        print("WARN: analog dump not found for +0x2c")
    else:
        t = t.replace(DUMP_OLD, DUMP_NEW, 1)
        print("csiphy: dump +0x2c")

    PHY.write_text(t)


if __name__ == "__main__":
    main()
