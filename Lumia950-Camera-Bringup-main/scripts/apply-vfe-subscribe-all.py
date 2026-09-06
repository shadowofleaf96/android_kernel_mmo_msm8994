#!/usr/bin/env python3
"""#113: HAL VIDIOC_SUBSCRIBE_EVENT type=0x1ff (CAF bitmask).
Keep the original 0x1ff subscribe (ioctl rc=0) and also subscribe
ISP_EVENT_SOF|iface, BUF_DONE, and BUF_DIVERT+stream_idx (kernel sends
ISP_EVENT_BUF_DIVERT + stream_idx). Extra failures must not change rc.
"""

from kernel_tree import kernel_tree, overlay_root
KERNEL_TREE = kernel_tree()
OVERLAY = overlay_root()

from pathlib import Path

UTIL = KERNEL_TREE / "drivers/media/platform/msm/camera_v2/isp/msm_isp_util.c"

NEW_FN = """int msm_isp_subscribe_event(struct v4l2_subdev *sd, struct v4l2_fh *fh,
	struct v4l2_event_subscription *sub)
{
	struct vfe_device *vfe_dev = v4l2_get_subdevdata(sd);
	int rc = 0;
	{
		static unsigned n;

		if (n < 8) {
			n++;
			pr_err("talkman_vfe subscribe n=%u type=0x%x id=%u flags=0x%x\\n",
				n, sub->type, sub->id, sub->flags);
		}
	}
	rc = v4l2_event_subscribe(fh, sub, MAX_ISP_V4l2_EVENTS, NULL);
	if (rc == 0) {
		if (sub->type == V4L2_EVENT_ALL ||
		    sub->type < ISP_EVENT_BASE) {
			int i;

			vfe_dev->axi_data.event_mask = 0;
			for (i = 0; i < ISP_EVENT_MAX; i++)
				vfe_dev->axi_data.event_mask |= (1 << i);
		} else {
			int event_idx = sub->type - ISP_EVENT_BASE;

			vfe_dev->axi_data.event_mask |= (1 << event_idx);
		}
	}
	/* HAL 0x1ff is a bitmask. Keep it subscribed so ioctl stays 0. */
	if (rc == 0 && sub->type && sub->type < ISP_EVENT_BASE) {
		struct v4l2_event_subscription extra = *sub;
		unsigned interface;
		unsigned stream;
		int extra_rc;

		for (interface = 0; interface < VFE_SRC_MAX; interface++) {
			extra.type = ISP_EVENT_SOF | interface;
			extra_rc = v4l2_event_subscribe(fh, &extra,
				MAX_ISP_V4l2_EVENTS, NULL);
			if (extra_rc)
				pr_err("talkman_vfe extra SOF|%u rc=%d\\n",
					interface, extra_rc);
		}
		extra.type = ISP_EVENT_BUF_DONE;
		extra_rc = v4l2_event_subscribe(fh, &extra,
			MAX_ISP_V4l2_EVENTS, NULL);
		if (extra_rc)
			pr_err("talkman_vfe extra BUF_DONE rc=%d\\n", extra_rc);
		for (stream = 0; stream < MAX_NUM_STREAM; stream++) {
			extra.type = ISP_EVENT_BUF_DIVERT + stream;
			extra_rc = v4l2_event_subscribe(fh, &extra,
				MAX_ISP_V4l2_EVENTS, NULL);
			if (extra_rc)
				pr_err("talkman_vfe extra DIVERT+%u rc=%d\\n",
					stream, extra_rc);
		}
		pr_err("talkman_vfe extra SOF+BUF_DONE+DIVERT after mask 0x%x rc0=%d\\n",
			sub->type, rc);
	}
	return rc;
}

"""


def main() -> None:
    t = UTIL.read_text()
    start = t.find("int msm_isp_subscribe_event(")
    end = t.find("int msm_isp_unsubscribe_event(")
    if start < 0 or end < 0 or end <= start:
        raise SystemExit("msm_isp_subscribe_event bounds not found")
    if "talkman_vfe extra SOF+BUF_DONE+DIVERT after mask" in t[start:end]:
        print("vfe additive SOF+DIVERT subscribe already present")
        return
    UTIL.write_text(t[:start] + NEW_FN + t[end:])
    print("vfe: keep 0x1ff subscribe, add SOF|iface + BUF_DONE + DIVERT")


if __name__ == "__main__":
    main()
