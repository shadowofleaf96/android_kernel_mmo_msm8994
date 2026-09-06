#!/usr/bin/env python3
"""#150: CSID TG data type 0x30 to match WP VF LUT CID0.

#149 4080 TG headers are valid (unmap DT 0x2B). LUT is 0x30 DPCM, so
nothing maps and preview stays black while TG is on. Force the
generator DT to 0x30. Hold TG 12s so a screenshot can catch it
(800ms is faster than adb). Same experiment, not a second CSI theory.
"""

from kernel_tree import kernel_tree, overlay_root
KERNEL_TREE = kernel_tree()
OVERLAY = overlay_root()

from pathlib import Path

CSID = KERNEL_TREE / "drivers/media/platform/msm/camera_v2/sensor/csid/msm_csid.c"

OLD = """		uint32_t dt = 0x2b, bpl, tgv;

		if (csid_params->lut_params.num_cid > 0 &&
		    csid_params->lut_params.vc_cfg[0])
			dt = csid_params->lut_params.vc_cfg[0]->dt;
"""

NEW = """		uint32_t dt = 0x2b, bpl, tgv;

		if (csid_params->lut_params.num_cid > 0 &&
		    csid_params->lut_params.vc_cfg[0])
			dt = csid_params->lut_params.vc_cfg[0]->dt;
		/* WP VF LUT CID0. HAL still asks TG for RAW10 0x2B. */
		dt = 0x30;
"""

OLD_OFF = """		schedule_delayed_work(&talkman_tg_off_dwork,
			msecs_to_jiffies(800));
		pr_err("talkman_csid tg will off WP 0xa06436 in 800ms\\n");
"""

NEW_OFF = """		schedule_delayed_work(&talkman_tg_off_dwork,
			msecs_to_jiffies(12000));
		pr_err("talkman_csid tg will off WP 0xa06436 in 12000ms\\n");
"""


def main() -> None:
    t = CSID.read_text()
    if "dt = 0x30;" in t and "WP VF LUT CID0" in t:
        print("csid TG DT 0x30 already present")
        return
    if OLD not in t:
        raise SystemExit("csid TG dt HAL lookup not found")
    t = t.replace(OLD, NEW, 1)
    if OLD_OFF not in t:
        raise SystemExit("csid TG 800ms off not found")
    t = t.replace(OLD_OFF, NEW_OFF, 1)
    CSID.write_text(t)
    print("csid: TG DT 0x30, off delay 12s (screenshot DPCM)")


if __name__ == "__main__":
    main()
