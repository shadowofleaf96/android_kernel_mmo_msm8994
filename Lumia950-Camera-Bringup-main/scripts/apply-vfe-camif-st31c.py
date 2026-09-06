#!/usr/bin/env python3
"""#89: matching geometry, no CAMIF error, never EOF.

Dump CAMIF_STATUS 0x31C on the first 8 SOF/EOF IRQs. Decode is
(lines << 16) | pixels (see notes/camif.md).
"""

from kernel_tree import kernel_tree, overlay_root
KERNEL_TREE = kernel_tree()
OVERLAY = overlay_root()

from pathlib import Path

VFE = KERNEL_TREE / "drivers/media/platform/msm/camera_v2/isp/msm_isp44.c"


def main() -> None:
    t = VFE.read_text()
    old = """			pr_err("talkman_vfe camif irq n=%d s0=0x%x sof=%d eof=%d fid=%u\\n",
				talkman_vfe_camif_irq, irq_status0,
				!!(irq_status0 & 1), !!(irq_status0 & 2),
				vfe_dev->axi_data.src_info[VFE_PIX_0].
					camif_sof_frame_id);
"""
    new = """			pr_err("talkman_vfe camif irq n=%d s0=0x%x s1=0x%x sof=%d eof=%d fid=%u st=0x%x\\n",
				talkman_vfe_camif_irq, irq_status0, irq_status1,
				!!(irq_status0 & 1), !!(irq_status0 & 2),
				vfe_dev->axi_data.src_info[VFE_PIX_0].
					camif_sof_frame_id,
				msm_camera_io_r(vfe_dev->vfe_base + 0x31C));
"""
    if "fid=%u st=0x%x" in t:
        print("vfe camif 0x31C SOF dump already present")
    elif old not in t:
        raise SystemExit("vfe44 camif irq pr_err not found")
    else:
        t = t.replace(old, new, 1)
        print("vfe44: CAMIF_STATUS 0x31C on SOF/EOF")
    VFE.write_text(t)


if __name__ == "__main__":
    main()
