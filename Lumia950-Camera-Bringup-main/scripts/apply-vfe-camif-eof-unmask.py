#!/usr/bin/env python3
"""#101: AXI composite/WM never fires. CAMIF SOF+EPOCH live, eof=0 in logs.

CAF ENABLE_CAMIF does val |= 0xF5 into irq_mask0 (0x28). 0xF5 is bits
0,2,4-7 — SOF and EPOCH0, NOT bit1 EOF. init_hardware_reg is 0xE00000F1,
also no bit1. read_irq_status masks status with 0x28, so we would never
see eof=1 even if the block asserted it. Bullhead uses the same mask
(AXI WM is a separate bit). Unmask bit1 so the existing camif irq log
can tell HW EOF from a masked IRQ.
"""

from kernel_tree import kernel_tree, overlay_root
KERNEL_TREE = kernel_tree()
OVERLAY = overlay_root()

from pathlib import Path

VFE = KERNEL_TREE / "drivers/media/platform/msm/camera_v2/isp/msm_isp44.c"

OLD = """		val = msm_camera_io_r(vfe_dev->vfe_base + 0x28);
		val |= 0xF5;
		msm_camera_io_w_mb(val, vfe_dev->vfe_base + 0x28);
"""
NEW = """		val = msm_camera_io_r(vfe_dev->vfe_base + 0x28);
		val |= 0xF7;
		msm_camera_io_w_mb(val, vfe_dev->vfe_base + 0x28);
		pr_err("talkman_vfe camif irq mask0=0x%x (EOF unmasked)\\n", val);
"""


def main() -> None:
    t = VFE.read_text()
    if "EOF unmasked" in t:
        print("vfe camif EOF unmask already present")
        return
    if OLD not in t:
        raise SystemExit("vfe44 ENABLE_CAMIF irq mask 0xF5 not found")
    t = t.replace(OLD, NEW, 1)
    VFE.write_text(t)
    print("vfe44: irq_mask0 |= 0xF7 (CAMIF EOF bit1)")


if __name__ == "__main__":
    main()
