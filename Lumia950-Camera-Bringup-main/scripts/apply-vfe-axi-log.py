#!/usr/bin/env python3
"""#100 killed CAMIF SOF with EFS syncMode. AXI buf_done never logged.

msm_isp_process_axi_irq is the PIX WM / composite-done path HAL needs
for preview. If this never fires while CAMIF SOF+EPOCH do, AXI waits
on CAMIF EOF (or WM never fills).
"""

from kernel_tree import kernel_tree, overlay_root
KERNEL_TREE = kernel_tree()
OVERLAY = overlay_root()

from pathlib import Path

AXI = KERNEL_TREE / "drivers/media/platform/msm/camera_v2/isp/msm_isp_axi_util.c"

OLD = """	if (!(comp_mask || wm_mask))
		return;

	ISP_DBG("%s: status: 0x%x\\n", __func__, irq_status0);
"""
NEW = """	if (!(comp_mask || wm_mask))
		return;

	{
		static unsigned n;

		if (n < 8) {
			n++;
			pr_err("talkman_vfe axi irq n=%u s0=0x%x s1=0x%x comp=0x%x wm=0x%x\\n",
				n, irq_status0, irq_status1, comp_mask, wm_mask);
		}
	}
	ISP_DBG("%s: status: 0x%x\\n", __func__, irq_status0);
"""


def main() -> None:
    t = AXI.read_text()
    if "talkman_vfe axi irq" in t:
        print("vfe axi irq log already present")
        return
    if OLD not in t:
        raise SystemExit("msm_isp_process_axi_irq mask check not found")
    t = t.replace(OLD, NEW, 1)
    AXI.write_text(t)
    print("vfe: AXI composite/WM irq log")


if __name__ == "__main__":
    main()
