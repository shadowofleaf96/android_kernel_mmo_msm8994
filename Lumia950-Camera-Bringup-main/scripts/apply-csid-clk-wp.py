#!/usr/bin/env python3
"""#147: WP CSI0 RCG CFG=0x105 is MMPLL0/3 = 266.67 MHz.

Linux DT qcom,clock-rates sets csi_clk (csi0_clk_src) to 240 MHz
(GPLL0/2.5). CSID looks up csi_src_clk which is the AHB phandle, so
clk_set_rate never touches the RCG. Force the clock named csi_clk
to the WP rate. Do not change VFE 320, CAMIF_CFG, or LUT in this flash.
"""

from kernel_tree import kernel_tree, overlay_root
KERNEL_TREE = kernel_tree()
OVERLAY = overlay_root()

from pathlib import Path

CSID = KERNEL_TREE / "drivers/media/platform/msm/camera_v2/sensor/csid/msm_csid.c"

OLD = """	rc = clk_set_rate(csid_clk_ptr[csid_dev->csid_clk_index],
				round_rate);
	if (rc < 0) {
		pr_err("csi_src_clk set failed\\n");
		return rc;
	}

	val = csid_params->lane_cnt - 1;
"""

NEW = """	rc = clk_set_rate(csid_clk_ptr[csid_dev->csid_clk_index],
				round_rate);
	if (rc < 0) {
		pr_err("csi_src_clk set failed\\n");
		return rc;
	}
	{
		int talkman_i;
		unsigned long talkman_wp = 266670000;

		/* DT names the RCG csi_clk (240 MHz). WP live is 266.67. */
		for (talkman_i = 0; talkman_i < csid_dev->num_clk; talkman_i++) {
			if (!csid_clk_info[talkman_i].clk_name ||
			    strcmp(csid_clk_info[talkman_i].clk_name, "csi_clk"))
				continue;
			round_rate = clk_round_rate(csid_clk_ptr[talkman_i],
						    talkman_wp);
			rc = clk_set_rate(csid_clk_ptr[talkman_i], round_rate);
			pr_err("talkman_csid wp csi_clk %lu round=%lu now=%lu rc=%d\\n",
				talkman_wp, round_rate,
				clk_get_rate(csid_clk_ptr[talkman_i]), rc);
			break;
		}
	}

	val = csid_params->lane_cnt - 1;
"""


def main() -> None:
    t = CSID.read_text()
    if "talkman_csid wp csi_clk" in t:
        print("csid WP 266.67 MHz already present")
        return
    if OLD not in t:
        raise SystemExit("csid clk_set_rate block not found")
    CSID.write_text(t.replace(OLD, NEW, 1))
    print("csid: force csi_clk 266670000 (WP CSI0 RCG)")


if __name__ == "__main__":
    main()
