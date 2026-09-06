#!/usr/bin/env python3
"""#100: CAMIF_CFG 0x2F8=0x48 killed CAMIF SOF/EPOCH. ISPIF PIX SOF still
37 fps. Bit 3 is a real sync field, but EFS with 0x2FC=0x00200040 does
not generate SOF on the ISPIF MIPI path. Revert to syncMode=0.
"""

from kernel_tree import kernel_tree, overlay_root
KERNEL_TREE = kernel_tree()
OVERLAY = overlay_root()

from pathlib import Path

VFE = KERNEL_TREE / "drivers/media/platform/msm/camera_v2/isp/msm_isp44.c"

BAD = """		val = msm_camera_io_r(vfe_dev->vfe_base + 0x2F8);
		val &= 0xFFFFFF3F;
		val = val | bus_en << 7 | vfe_en << 6;
		val |= 0x8;
		msm_camera_io_w(val, vfe_dev->vfe_base + 0x2F8);
		pr_err("talkman_vfe camif cfg 0x2f8=0x%x (syncMode EFS)\\n", val);
"""
GOOD = """		val = msm_camera_io_r(vfe_dev->vfe_base + 0x2F8);
		val &= 0xFFFFFF3F;
		val = val | bus_en << 7 | vfe_en << 6;
		msm_camera_io_w(val, vfe_dev->vfe_base + 0x2F8);
"""


def main() -> None:
    t = VFE.read_text()
    if "syncMode EFS" not in t:
        print("vfe camif syncMode EFS already reverted")
        return
    if BAD not in t:
        raise SystemExit("vfe44 EFS syncMode block not found")
    t = t.replace(BAD, GOOD, 1)
    VFE.write_text(t)
    print("vfe44: reverted CAMIF_CFG syncMode EFS")


if __name__ == "__main__":
    main()
