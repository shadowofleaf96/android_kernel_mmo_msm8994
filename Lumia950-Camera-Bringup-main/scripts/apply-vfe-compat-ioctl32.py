#!/usr/bin/env python3
"""#111 bootlooped: compat_ioctl32 = v4l2_compat_ioctl32. MSM custom
ioctls hit v4l2_compat default, which calls vdev->fops->compat_ioctl32
again (itself) until the stack dies. qcamerasvr opens VFE at boot.

Keep the old MSM ioctl path. Only VIDIOC_DQEVENT / DQEVENT32 (nr 89)
go through v4l2_compat_ioctl32, which handles those in its switch and
does not recurse.
"""

from kernel_tree import kernel_tree, overlay_root
KERNEL_TREE = kernel_tree()
OVERLAY = overlay_root()

from pathlib import Path

ISP = KERNEL_TREE / "drivers/media/platform/msm/camera_v2/isp/msm_isp.c"

OLD_ASSIGN = """	.compat_ioctl32 = msm_isp_subdev_fops_ioctl,
"""
NEW_ASSIGN = """	.compat_ioctl32 = msm_isp_subdev_fops_compat_ioctl,
"""

# Also undo the bootloop assignment if it is still in the WSL tree.
LOOP_ASSIGN = """	.compat_ioctl32 = v4l2_compat_ioctl32,
"""

WRAPPER = """
#ifdef CONFIG_COMPAT
static long msm_isp_subdev_fops_compat_ioctl(struct file *file,
	unsigned int cmd, unsigned long arg)
{
	/* nr 89 = DQEVENT. 32-bit daemon uses VIDIOC_DQEVENT32 (different
	 * _IOC_SIZE). Do not send MSM custom ioctls through
	 * v4l2_compat_ioctl32: its default calls fops->compat_ioctl32
	 * and recurses (#111 bootloop).
	 */
	if (_IOC_TYPE(cmd) == 'V' && _IOC_NR(cmd) == 89)
		return v4l2_compat_ioctl32(file, cmd, arg);
	return msm_isp_subdev_fops_ioctl(file, cmd, arg);
}
#endif

"""

OLD_FOPS_IOCTL = """static long msm_isp_subdev_fops_ioctl(struct file *file, unsigned int cmd,
	unsigned long arg)
{
	return video_usercopy(file, cmd, arg, msm_isp_subdev_do_ioctl);
}
"""


def main() -> None:
    t = ISP.read_text()
    has_fn = "static long msm_isp_subdev_fops_compat_ioctl(" in t
    if has_fn and LOOP_ASSIGN not in t and NEW_ASSIGN in t:
        print("vfe DQEVENT32 wrapper already present")
        return
    if not has_fn:
        if OLD_FOPS_IOCTL not in t:
            raise SystemExit("msm_isp_subdev_fops_ioctl not found")
        t = t.replace(OLD_FOPS_IOCTL, OLD_FOPS_IOCTL + WRAPPER, 1)
    t = t.replace(LOOP_ASSIGN, NEW_ASSIGN)
    if OLD_ASSIGN in t:
        t = t.replace(OLD_ASSIGN, NEW_ASSIGN, 1)
    if NEW_ASSIGN not in t:
        raise SystemExit("compat_ioctl32 assignment not found")
    if "static long msm_isp_subdev_fops_compat_ioctl(" not in t:
        raise SystemExit("compat wrapper function missing")
    ISP.write_text(t)
    print("vfe: compat wrapper, DQEVENT32 only (no recurse)")


if __name__ == "__main__":
    main()
