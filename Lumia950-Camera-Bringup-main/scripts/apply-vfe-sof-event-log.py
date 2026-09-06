#!/usr/bin/env python3
"""#109: epoch0 line 20, AXI buf_done, HAL still SOF-freezes. Kernel
msm_isp_notify -> v4l2_event_queue. 32-bit daemon has compat DQEVENT.
If DQEVENT never runs, ISP userspace is not polling the VFE node.
If it dequeues SOF, freeze is MCT not consuming the event.
"""

from kernel_tree import kernel_tree, overlay_root
KERNEL_TREE = kernel_tree()
OVERLAY = overlay_root()

from pathlib import Path

ISP = KERNEL_TREE / "drivers/media/platform/msm/camera_v2/isp/msm_isp.c"
AXI = KERNEL_TREE / "drivers/media/platform/msm/camera_v2/isp/msm_isp_axi_util.c"

DQ_OLD = """		rc = v4l2_event_dequeue(vfh, &isp_event,
				file->f_flags & O_NONBLOCK);
		if (rc)
			return rc;
"""
DQ_NEW = """		rc = v4l2_event_dequeue(vfh, &isp_event,
				file->f_flags & O_NONBLOCK);
		{
			static unsigned n;

			if (n < 8) {
				n++;
				pr_err("talkman_vfe dqevent n=%u rc=%ld type=0x%x\\n",
					n, rc, rc ? 0 : isp_event.type);
			}
		}
		if (rc)
			return rc;
"""

SEND_OLD = """	event_data.frame_id = vfe_dev->axi_data.src_info[frame_src].frame_id;
	event_data.timestamp = ts->event_time;
	event_data.mono_timestamp = ts->buf_time;
	msm_isp_send_event(vfe_dev, event_type | frame_src, &event_data);
"""
SEND_NEW = """	event_data.frame_id = vfe_dev->axi_data.src_info[frame_src].frame_id;
	event_data.timestamp = ts->event_time;
	event_data.mono_timestamp = ts->buf_time;
	if (event_type == ISP_EVENT_SOF) {
		static unsigned n;

		if (n < 8) {
			n++;
			pr_err("talkman_vfe send SOF n=%u src=%u fid=%u type=0x%x\\n",
				n, frame_src, event_data.frame_id,
				event_type | frame_src);
		}
	}
	msm_isp_send_event(vfe_dev, event_type | frame_src, &event_data);
"""


def main() -> None:
    isp = ISP.read_text()
    if "talkman_vfe dqevent n=" in isp:
        print("vfe dqevent log already present")
    elif DQ_OLD not in isp:
        raise SystemExit("compat dqevent dequeue not found")
    else:
        ISP.write_text(isp.replace(DQ_OLD, DQ_NEW, 1))
        print("vfe: compat DQEVENT log")

    axi = AXI.read_text()
    if "talkman_vfe send SOF n=" in axi:
        print("vfe send SOF log already present")
        return
    if SEND_OLD not in axi:
        raise SystemExit("msm_isp_notify send_event tail not found")
    AXI.write_text(axi.replace(SEND_OLD, SEND_NEW, 1))
    print("vfe: notify SOF send log")


if __name__ == "__main__":
    main()
