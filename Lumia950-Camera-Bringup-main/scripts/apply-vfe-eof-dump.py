#!/usr/bin/env python3
"""#103 dump: modules on, WM0 enabled, NV12 xbar, 1200-line preview size.
AXI still never fires. Need ping/pong IOVA and framedrop pattern.
"""

from kernel_tree import kernel_tree, overlay_root
KERNEL_TREE = kernel_tree()
OVERLAY = overlay_root()

from pathlib import Path

VFE = KERNEL_TREE / "drivers/media/platform/msm/camera_v2/isp/msm_isp44.c"

OLD = """			pr_err("talkman_vfe eof dump mod=0x%x io=0x%x ping=0x%x comp=0x%x mask=0x%x wm0=0x%x img=0x%x xbar=0x%x\\n",
				msm_camera_io_r(vfe_dev->vfe_base + 0x18),
				msm_camera_io_r(vfe_dev->vfe_base + 0x54),
				msm_camera_io_r(vfe_dev->vfe_base + 0x268),
				msm_camera_io_r(vfe_dev->vfe_base + 0x40),
				msm_camera_io_r(vfe_dev->vfe_base + 0x28),
				msm_camera_io_r(vfe_dev->vfe_base + 0x6C),
				msm_camera_io_r(vfe_dev->vfe_base + 0x80),
				msm_camera_io_r(vfe_dev->vfe_base + 0x58));
"""
NEW = """			pr_err("talkman_vfe eof dump mod=0x%x io=0x%x pingst=0x%x comp=0x%x mask=0x%x wm0=0x%x img=0x%x xbar=0x%x\\n",
				msm_camera_io_r(vfe_dev->vfe_base + 0x18),
				msm_camera_io_r(vfe_dev->vfe_base + 0x54),
				msm_camera_io_r(vfe_dev->vfe_base + 0x268),
				msm_camera_io_r(vfe_dev->vfe_base + 0x40),
				msm_camera_io_r(vfe_dev->vfe_base + 0x28),
				msm_camera_io_r(vfe_dev->vfe_base + 0x6C),
				msm_camera_io_r(vfe_dev->vfe_base + 0x80),
				msm_camera_io_r(vfe_dev->vfe_base + 0x58));
			pr_err("talkman_vfe eof wm ping=0x%x pong=0x%x addr=0x%x buf=0x%x drop=0x%x cfg2f8=0x%x reload=0x%x\\n",
				msm_camera_io_r(vfe_dev->vfe_base + 0x70),
				msm_camera_io_r(vfe_dev->vfe_base + 0x74),
				msm_camera_io_r(vfe_dev->vfe_base + 0x78),
				msm_camera_io_r(vfe_dev->vfe_base + 0x84),
				msm_camera_io_r(vfe_dev->vfe_base + 0x88),
				msm_camera_io_r(vfe_dev->vfe_base + 0x2F8),
				msm_camera_io_r(vfe_dev->vfe_base + 0x4C));
"""


def main() -> None:
    t = VFE.read_text()
    if "talkman_vfe eof wm ping=" in t:
        print("vfe eof wm ping dump already present")
        return
    if OLD not in t:
        raise SystemExit("vfe44 first-EOF dump pr_err not found")
    t = t.replace(OLD, NEW, 1)
    VFE.write_text(t)
    print("vfe44: first-EOF ping/framedrop dump")


if __name__ == "__main__":
    main()
