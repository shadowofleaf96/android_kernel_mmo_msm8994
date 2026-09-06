#!/usr/bin/env python3
"""#108: AXI buf_done + EPOCH0 every frame, but mm-camera still SOF-freezes.
CAF ENABLE_CAMIF programs epoch0 at line 20 (0x140000). #95 moved it to
3027 to prove CAMIF reached full height. HAL SOF is that EPOCH0 notify;
an epoch at last_line races buf_done and is not the bullhead contract.
Put epoch back at line 20 now that CAMIF geometry is proven.
"""

from kernel_tree import kernel_tree, overlay_root
KERNEL_TREE = kernel_tree()
OVERLAY = overlay_root()

from pathlib import Path

VFE = KERNEL_TREE / "drivers/media/platform/msm/camera_v2/isp/msm_isp44.c"


def main() -> None:
    t = VFE.read_text()
    changed = False
    if "0x0BD30000, vfe_dev->vfe_base + 0x318" in t:
        t = t.replace(
            "0x0BD30000, vfe_dev->vfe_base + 0x318",
            "0x140000, vfe_dev->vfe_base + 0x318",
        )
        changed = True
    t2 = t.replace(
        'pr_err("talkman_vfe camif epoch0=3027\\n");\n',
        "",
    )
    if t2 != t:
        t = t2
        changed = True
    if 'pr_err("talkman_vfe camif epoch0=20\\n");' not in t:
        t = t.replace(
            "msm_camera_io_w_mb(0x140000, vfe_dev->vfe_base + 0x318);",
            "msm_camera_io_w_mb(0x140000, vfe_dev->vfe_base + 0x318);\n"
            '\t\tpr_err("talkman_vfe camif epoch0=20\\n");',
            1,
        )
        changed = True
    if changed:
        VFE.write_text(t)
        print("vfe44: epoch0 line 20 (HAL SOF contract)")
    else:
        print("vfe camif epoch0 20 already restored")


if __name__ == "__main__":
    main()
