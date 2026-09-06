#!/usr/bin/env python3
"""#148: match WP VF CAMSS CGC enables and dump leftover MMCC/TCSR.

dump-vf.log (Hill preview):
  CGC 0xFDA00000 mux +0x20/28/30/38/40 = 0 (do not lottery)
  enables +0x24/2c/34/3c/44 = 0xf / 0x3f / 3 / 3 / 3
  CSI0 RCG CFG = 0x105 (266.67, #147)
  PHYTIMER CFG = 0x107 (200 MHz)
  CSI_VFE0 CBCR = 0x4ff1
  0xFD512028 = 0x009690e1 (chip id, read-only)

Linux never writes the CAMSS CGC enables. PHY analog is programmed
after this so the gates are on first. Do not write mux or TCSR.
"""

from kernel_tree import kernel_tree, overlay_root
KERNEL_TREE = kernel_tree()
OVERLAY = overlay_root()

from pathlib import Path

PHY = KERNEL_TREE / "drivers/media/platform/msm/camera_v2/sensor/csiphy/msm_csiphy.c"

OLD = """	if (rc < 0) {
		pr_err("csiphy_timer_src_clk set failed\\n");
		return rc;
	}

	CDBG("%s csiphy_params, mask = 0x%x cnt = %d\\n",
"""

NEW = """	if (rc < 0) {
		pr_err("csiphy_timer_src_clk set failed\\n");
		return rc;
	}
	{
		void __iomem *cgc = ioremap(0xFDA00000, 0x50);
		void __iomem *mmcc = ioremap(0xFD8C3000, 0x800);
		void __iomem *tcsr = ioremap(0xFD512028, 4);

		if (cgc) {
			pr_err("talkman_cgc before 00=%x 10=%x 20=%x 24=%x 28=%x 2c=%x 30=%x 34=%x 38=%x 3c=%x 40=%x 44=%x\\n",
				msm_camera_io_r(cgc),
				msm_camera_io_r(cgc + 0x10),
				msm_camera_io_r(cgc + 0x20),
				msm_camera_io_r(cgc + 0x24),
				msm_camera_io_r(cgc + 0x28),
				msm_camera_io_r(cgc + 0x2c),
				msm_camera_io_r(cgc + 0x30),
				msm_camera_io_r(cgc + 0x34),
				msm_camera_io_r(cgc + 0x38),
				msm_camera_io_r(cgc + 0x3c),
				msm_camera_io_r(cgc + 0x40),
				msm_camera_io_r(cgc + 0x44));
			/* WP VF enables. Mux stays 0. */
			msm_camera_io_w(0xf, cgc + 0x24);
			msm_camera_io_w(0x3f, cgc + 0x2c);
			msm_camera_io_w(3, cgc + 0x34);
			msm_camera_io_w(3, cgc + 0x3c);
			msm_camera_io_w(3, cgc + 0x44);
			mb();
			pr_err("talkman_cgc after 24=%x 2c=%x 34=%x 3c=%x 44=%x\\n",
				msm_camera_io_r(cgc + 0x24),
				msm_camera_io_r(cgc + 0x2c),
				msm_camera_io_r(cgc + 0x34),
				msm_camera_io_r(cgc + 0x3c),
				msm_camera_io_r(cgc + 0x44));
			iounmap(cgc);
		} else
			pr_err("talkman_cgc ioremap fail\\n");
		if (mmcc) {
			pr_err("talkman_mmcc phy=%x csi0=%x csi0_cbcr=%x csi_vfe0=%x vfe0=%x mclk0=%x\\n",
				msm_camera_io_r(mmcc + 0x4),
				msm_camera_io_r(mmcc + 0x94),
				msm_camera_io_r(mmcc + 0xb4),
				msm_camera_io_r(mmcc + 0x704),
				msm_camera_io_r(mmcc + 0x604),
				msm_camera_io_r(mmcc + 0x364));
			iounmap(mmcc);
		}
		if (tcsr) {
			pr_err("talkman_tcsr fd512028=%x (WP 009690e1)\\n",
				msm_camera_io_r(tcsr));
			iounmap(tcsr);
		}
	}

	CDBG("%s csiphy_params, mask = 0x%x cnt = %d\\n",
"""


def main() -> None:
    t = PHY.read_text()
    if "talkman_cgc before" in t:
        print("csiphy WP CGC enables already present")
        return
    if OLD not in t:
        raise SystemExit("csiphy timer clk_set_rate tail not found")
    PHY.write_text(t.replace(OLD, NEW, 1))
    print("csiphy: WP CGC enables + MMCC/TCSR dump")


if __name__ == "__main__":
    main()
