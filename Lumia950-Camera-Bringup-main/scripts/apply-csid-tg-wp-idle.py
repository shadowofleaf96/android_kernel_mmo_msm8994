#!/usr/bin/env python3
"""WP never enables CSID TG. Linux TG-off after 0xa06437 still 0x20000dd.
102/103 left TG_CTRL at 0, which kills PIX. Write WP idle 0xa06436 and
leave talkman_tg=0 so CSID is never in test-gen mode.
"""

from kernel_tree import kernel_tree, overlay_root
KERNEL_TREE = kernel_tree()
OVERLAY = overlay_root()

from pathlib import Path

CSID = KERNEL_TREE / "drivers/media/platform/msm/camera_v2/sensor/csid/msm_csid.c"

OLD_STAY = """	if (talkman_tg > 0) {
		msm_camera_io_w(0x00A06437, csidbase +
			csid_dev->ctrl_reg->csid_reg.csid_tg_ctrl_addr);
		pr_err("talkman_csid tg enable 0xa06437\\n");
		pr_err("talkman_csid tg stay on (PHY 0x20000dd)\\n");
	}
"""

OLD_EN = """	if (talkman_tg > 0) {
		msm_camera_io_w(0x00A06437, csidbase +
			csid_dev->ctrl_reg->csid_reg.csid_tg_ctrl_addr);
		pr_err("talkman_csid tg enable 0xa06437\\n");
	}
"""

OLD_SCHED = """	if (talkman_tg > 0) {
		msm_camera_io_w(0x00A06437, csidbase +
			csid_dev->ctrl_reg->csid_reg.csid_tg_ctrl_addr);
		pr_err("talkman_csid tg enable 0xa06437\\n");
		/* #109 analog stuck. Sample PHY after HAL has SOF. */
		talkman_tg_off_dev = csid_dev;
		schedule_delayed_work(&talkman_tg_off_dwork,
			msecs_to_jiffies(800));
		pr_err("talkman_csid tg will off WP 0xa06436 in 800ms\\n");
	}
"""

NEW = """	if (talkman_tg > 0) {
		msm_camera_io_w(0x00A06437, csidbase +
			csid_dev->ctrl_reg->csid_reg.csid_tg_ctrl_addr);
		pr_err("talkman_csid tg enable 0xa06437\\n");
	} else {
		/* WP FUN_0041ddd4: TG_CTRL idle 0xa06436, never 0xa06437.
		 * TG_CTRL=0 (#102/#105) killed PIX including PHY. */
		msm_camera_io_w(0x00A06436, csidbase +
			csid_dev->ctrl_reg->csid_reg.csid_tg_ctrl_addr);
		pr_err("talkman_csid tg WP disable 0xa06436 (never on)\\n");
	}
"""


def main() -> None:
    t = CSID.read_text()
    if "static int talkman_tg = 1;" in t:
        print("csid TG stays on (WP idle else-branch only if tg=0)")
    elif "static int talkman_tg = 0;" in t:
        t = t.replace("static int talkman_tg = 0;",
                      "static int talkman_tg = 1;", 1)
        print("csid: talkman_tg=1 (112 never-TG froze at table 5)")
    else:
        raise SystemExit("talkman_tg not found")

    if "talkman_csid tg WP disable 0xa06436 (never on)" in t:
        CSID.write_text(t)
        print("csid WP TG_CTRL idle already present")
        return

    if OLD_STAY in t:
        t = t.replace(OLD_STAY, NEW, 1)
        print("csid: WP TG_CTRL 0xa06436 when TG off (was stay-on)")
    elif OLD_SCHED in t:
        t = t.replace(OLD_SCHED, NEW, 1)
        print("csid: WP TG_CTRL 0xa06436 when TG off (was auto-off)")
    elif OLD_EN in t:
        t = t.replace(OLD_EN, NEW, 1)
        print("csid: WP TG_CTRL 0xa06436 when TG off")
    else:
        CSID.write_text(t)
        raise SystemExit("tg enable block not found")
    CSID.write_text(t)


if __name__ == "__main__":
    main()
