#!/usr/bin/env python3
"""#90: CAMIF_STATUS 0x31C is 0 at SOF (cleared on FV). Sample 10 ms later."""

from kernel_tree import kernel_tree, overlay_root
KERNEL_TREE = kernel_tree()
OVERLAY = overlay_root()

from pathlib import Path

VFE = KERNEL_TREE / "drivers/media/platform/msm/camera_v2/isp/msm_isp44.c"

MID_FN = """
static struct vfe_device *talkman_vfe_mid_dev;
static void talkman_vfe_camif_mid(struct work_struct *w)
{
	static int n;
	struct vfe_device *vfe_dev = talkman_vfe_mid_dev;
	uint32_t st, extra;

	if (!vfe_dev || !vfe_dev->vfe_base || n >= 8)
		return;
	(void)w;
	n++;
	st = msm_camera_io_r(vfe_dev->vfe_base + 0x31C);
	extra = msm_camera_io_r(vfe_dev->vfe_base + 0x320);
	pr_err("talkman_vfe camif mid n=%d st=0x%x extra=0x%x cmd=0x%x cfg=0x%x\\n",
		n, st, extra,
		msm_camera_io_r(vfe_dev->vfe_base + 0x2F4),
		msm_camera_io_r(vfe_dev->vfe_base + 0x2F8));
}
static DECLARE_DELAYED_WORK(talkman_vfe_camif_mid_w, talkman_vfe_camif_mid);
"""


def main() -> None:
    t = VFE.read_text()
    old_inc = """#include "msm_camera_io_util.h"

#undef CDBG
"""
    new_inc = """#include "msm_camera_io_util.h"
""" + MID_FN + """
#undef CDBG
"""
    if "talkman_vfe camif mid n=" in t:
        print("vfe camif mid-frame dump already present")
        return
    if old_inc not in t:
        raise SystemExit("vfe44 include/CDBG block not found")
    t = t.replace(old_inc, new_inc, 1)

    old_irq = """				msm_camera_io_r(vfe_dev->vfe_base + 0x31C));
"""
    new_irq = """				msm_camera_io_r(vfe_dev->vfe_base + 0x31C));
			talkman_vfe_mid_dev = vfe_dev;
			mod_delayed_work(system_wq, &talkman_vfe_camif_mid_w,
				msecs_to_jiffies(10));
"""
    if old_irq not in t:
        raise SystemExit("vfe44 0x31C irq read not found")
    t = t.replace(old_irq, new_irq, 1)
    VFE.write_text(t)
    print("vfe44: CAMIF mid-frame 0x31C dump")


if __name__ == "__main__":
    main()
