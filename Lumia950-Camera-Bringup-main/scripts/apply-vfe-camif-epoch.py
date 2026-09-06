#!/usr/bin/env python3
"""#95: EFS 0x2FC written; still SOF without EOF.

ENABLE_CAMIF hardcodes epoch 0x318 = 0x140000 (line 20, IMX377 dummy).
HAL PIX SOF notify is EPOCH0 (msm_isp_notify), not CAMIF bit0.
Move epoch0 to last_line 3027 (0xBD3<<16). If EPOCH0 fires, CAMIF
reached full height. If not, the line counter never gets there.
"""

from kernel_tree import kernel_tree, overlay_root
KERNEL_TREE = kernel_tree()
OVERLAY = overlay_root()

from pathlib import Path

VFE = KERNEL_TREE / "drivers/media/platform/msm/camera_v2/isp/msm_isp44.c"


def main() -> None:
    t = VFE.read_text()
    # #109: HAL SOF-freezes with epoch at last_line. Keep CAF line 20.
    # Do not convert 0x140000 -> 0x0BD30000 anymore.
    print("vfe camif epoch0 3027 diagnostic retired (HAL needs line 20)")

    old_ep = """	if (irq_status0 & BIT(2)) {
		msm_isp_notify(vfe_dev, ISP_EVENT_SOF, VFE_PIX_0, ts);
		ISP_DBG("%s: EPOCH0 IRQ\\n", __func__);
"""
    new_ep = """	if (irq_status0 & BIT(2)) {
		static int talkman_vfe_epoch;

		if (talkman_vfe_epoch < 8) {
			talkman_vfe_epoch++;
			pr_err("talkman_vfe camif EPOCH0 n=%d s0=0x%x fid=%u\\n",
				talkman_vfe_epoch, irq_status0,
				vfe_dev->axi_data.src_info[VFE_PIX_0].
					camif_sof_frame_id);
		}
		msm_isp_notify(vfe_dev, ISP_EVENT_SOF, VFE_PIX_0, ts);
		ISP_DBG("%s: EPOCH0 IRQ\\n", __func__);
"""
    if "talkman_vfe camif EPOCH0 n=" in t:
        print("vfe camif EPOCH0 log already present")
    elif old_ep not in t:
        raise SystemExit("vfe44 EPOCH0 handler not found")
    else:
        t = t.replace(old_ep, new_ep, 1)
        print("vfe44: EPOCH0 log")

    VFE.write_text(t)


if __name__ == "__main__":
    main()
