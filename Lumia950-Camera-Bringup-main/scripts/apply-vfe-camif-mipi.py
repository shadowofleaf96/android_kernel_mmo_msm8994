#!/usr/bin/env python3
"""#98: last_line=3026 (epoch in V-blank) still never CAMIF EOF.

0x2E8 live dump is 0x7. CAF does val |= camif_input (MIPI=3).
Mainline camss-vfe-4-1 writes MIPI_EN=0x3 only. Bit 2 is RDI_EN
(VFE_0_RDI_CFG_x_RDI_EN_BIT). PIX CAMIF should not set RDI_EN.
"""

from kernel_tree import kernel_tree, overlay_root
KERNEL_TREE = kernel_tree()
OVERLAY = overlay_root()

from pathlib import Path

VFE = KERNEL_TREE / "drivers/media/platform/msm/camera_v2/isp/msm_isp44.c"

OLD = """	val = msm_camera_io_r(vfe_dev->vfe_base + 0x2E8);
	val |= camif_cfg->camif_input;
	msm_camera_io_w(val, vfe_dev->vfe_base + 0x2E8);
"""
NEW = """	val = msm_camera_io_r(vfe_dev->vfe_base + 0x2E8);
	val |= camif_cfg->camif_input;
	val = 0x3;
	msm_camera_io_w(val, vfe_dev->vfe_base + 0x2E8);
	pr_err("talkman_vfe camif 0x2e8=0x3 (MIPI_EN, no RDI_EN)\\n");
"""


def main() -> None:
    t = VFE.read_text()
    if "talkman_vfe camif 0x2e8=0x3" in t:
        print("vfe camif 0x2E8 MIPI_EN already present")
        return
    if OLD not in t:
        raise SystemExit("vfe44 0x2E8 camif_input OR not found")
    t = t.replace(OLD, NEW, 1)
    VFE.write_text(t)
    print("vfe44: 0x2E8 = 0x3 MIPI_EN")


if __name__ == "__main__":
    main()
