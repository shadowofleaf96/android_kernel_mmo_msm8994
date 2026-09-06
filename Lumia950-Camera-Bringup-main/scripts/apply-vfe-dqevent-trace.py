#!/usr/bin/env python3
"""#112: DQEVENT32 wrap booted, still no msm_isp_dqevent log. Either HAL
never issues nr 89, or dequeue blocks before the post-dequeue print.
Log wrapper cmds, subscribe, and dqevent entry.
"""

from kernel_tree import kernel_tree, overlay_root
KERNEL_TREE = kernel_tree()
OVERLAY = overlay_root()

from pathlib import Path

ISP = KERNEL_TREE / "drivers/media/platform/msm/camera_v2/isp/msm_isp.c"
UTIL = KERNEL_TREE / "drivers/media/platform/msm/camera_v2/isp/msm_isp_util.c"

WRAP_OLD = """	if (_IOC_TYPE(cmd) == 'V' && _IOC_NR(cmd) == 89)
		return v4l2_compat_ioctl32(file, cmd, arg);
	return msm_isp_subdev_fops_ioctl(file, cmd, arg);
"""
WRAP_NEW = """	{
		static unsigned n;
		unsigned nr = _IOC_NR(cmd);

		if (n < 24 || (_IOC_TYPE(cmd) == 'V' && nr == 89)) {
			n++;
			pr_err("talkman_vfe compat ioctl n=%u cmd=0x%x type=%c nr=%u\\n",
				n, cmd, (char)_IOC_TYPE(cmd), nr);
		}
	}
	if (_IOC_TYPE(cmd) == 'V' && _IOC_NR(cmd) == 89)
		return v4l2_compat_ioctl32(file, cmd, arg);
	return msm_isp_subdev_fops_ioctl(file, cmd, arg);
"""

DQ_OLD = """	long rc;
	if (is_compat_task()) {
		struct msm_isp_event_data32 *event_data32;
		struct msm_isp_event_data  *event_data;
		struct v4l2_event isp_event;
		struct v4l2_event *isp_event_user;

		memset(&isp_event, 0, sizeof(isp_event));
		rc = v4l2_event_dequeue(vfh, &isp_event,
"""
DQ_NEW = """	long rc;
	{
		static unsigned n;

		if (n < 8) {
			n++;
			pr_err("talkman_vfe dqevent enter n=%u compat=%d\\n",
				n, is_compat_task());
		}
	}
	if (is_compat_task()) {
		struct msm_isp_event_data32 *event_data32;
		struct msm_isp_event_data  *event_data;
		struct v4l2_event isp_event;
		struct v4l2_event *isp_event_user;

		memset(&isp_event, 0, sizeof(isp_event));
		rc = v4l2_event_dequeue(vfh, &isp_event,
"""

SUB_OLD = """	int rc = 0;
	rc = v4l2_event_subscribe(fh, sub, MAX_ISP_V4l2_EVENTS, NULL);
"""
SUB_NEW = """	int rc = 0;
	{
		static unsigned n;

		if (n < 8) {
			n++;
			pr_err("talkman_vfe subscribe n=%u type=0x%x id=%u flags=0x%x\\n",
				n, sub->type, sub->id, sub->flags);
		}
	}
	rc = v4l2_event_subscribe(fh, sub, MAX_ISP_V4l2_EVENTS, NULL);
"""


def main() -> None:
    t = ISP.read_text()
    if "talkman_vfe compat ioctl n=" in t:
        print("vfe compat ioctl log already present")
    elif WRAP_OLD not in t:
        raise SystemExit("compat wrapper body not found")
    else:
        t = t.replace(WRAP_OLD, WRAP_NEW, 1)
        print("vfe: compat ioctl log")
    if "talkman_vfe dqevent enter n=" in t:
        print("vfe dqevent enter log already present")
    elif DQ_OLD not in t:
        raise SystemExit("msm_isp_dqevent compat dequeue not found")
    else:
        t = t.replace(DQ_OLD, DQ_NEW, 1)
        print("vfe: dqevent enter log")
    ISP.write_text(t)

    u = UTIL.read_text()
    if "talkman_vfe subscribe n=" in u:
        print("vfe subscribe log already present")
        return
    if SUB_OLD not in u:
        raise SystemExit("msm_isp_subscribe_event not found")
    UTIL.write_text(u.replace(SUB_OLD, SUB_NEW, 1))
    print("vfe: subscribe log")


if __name__ == "__main__":
    main()
