#!/usr/bin/env python3
"""#105: framedrop keep-all immediately halts CAMIF (cmd=0x6, 0x31C Halt).
CAF overflow path zeros irq_status before process_error_irq, so dmesg
never named the bit. Log overflow_mask.
"""

from kernel_tree import kernel_tree, overlay_root
KERNEL_TREE = kernel_tree()
OVERLAY = overlay_root()

from pathlib import Path

UTIL = KERNEL_TREE / "drivers/media/platform/msm/camera_v2/isp/msm_isp_util.c"

OLD = """	if (overflow_mask) {
		struct msm_isp_event_data error_event;
"""
NEW = """	if (overflow_mask) {
		struct msm_isp_event_data error_event;

		pr_err("talkman_vfe overflow mask=0x%x s0=0x%x s1=0x%x\\n",
			overflow_mask, *irq_status0, *irq_status1);
"""


def main() -> None:
    t = UTIL.read_text()
    if "talkman_vfe overflow mask=" in t:
        print("vfe overflow log already present")
        return
    if OLD not in t:
        raise SystemExit("msm_isp overflow_mask block not found")
    t = t.replace(OLD, NEW, 1)
    UTIL.write_text(t)
    print("vfe: bus overflow mask log")


if __name__ == "__main__":
    main()
