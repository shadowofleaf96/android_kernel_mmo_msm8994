#!/usr/bin/env python3
"""Clamp VFE pixclk to 600 MHz (msm8992 ftbl_vfe0_clk_src HIGH).

Research:
- clock-mmss-8992.c: 80/100/200/320/480/600 MHz. HIGH fmax is 600.
- #92 200 MHz: overflow 5624 px. #93 320 MHz: overflow 6728 px.
- #86/#91 480 MHz (HAL 424.8 rounded): no overflow, never EOF.
- TG SOF ~37 fps * 4088 * 3028 ≈ 458 Mpix/s. 480 MHz is ~5% headroom
  with HAL hbi=0. QCOM IFE clock guide: too-low clock => CAMIF overflow;
  clock must cover min HBI (64), not average. 600 MHz is the remaining
  table step above the measured rate.
"""

from kernel_tree import kernel_tree, overlay_root
KERNEL_TREE = kernel_tree()
OVERLAY = overlay_root()

from pathlib import Path

UTIL = KERNEL_TREE / "drivers/media/platform/msm/camera_v2/isp/msm_isp_util.c"

OLD320 = """	if (vfe_dev->axi_data.src_info[VFE_PIX_0].pixel_clock > 320000000) {
		pr_err("talkman_vfe pixclk %ld -> 320000000\\n",
			vfe_dev->axi_data.src_info[VFE_PIX_0].pixel_clock);
		vfe_dev->axi_data.src_info[VFE_PIX_0].pixel_clock = 320000000;
	}
"""
OLD200 = """	if (vfe_dev->axi_data.src_info[VFE_PIX_0].pixel_clock > 200000000) {
		pr_err("talkman_vfe pixclk %ld -> 200000000\\n",
			vfe_dev->axi_data.src_info[VFE_PIX_0].pixel_clock);
		vfe_dev->axi_data.src_info[VFE_PIX_0].pixel_clock = 200000000;
	}
"""
NEW600 = """	if (vfe_dev->axi_data.src_info[VFE_PIX_0].pixel_clock != 600000000) {
		pr_err("talkman_vfe pixclk %ld -> 600000000\\n",
			vfe_dev->axi_data.src_info[VFE_PIX_0].pixel_clock);
		vfe_dev->axi_data.src_info[VFE_PIX_0].pixel_clock = 600000000;
	}
"""
FRESH_OLD = """	vfe_dev->axi_data.src_info[VFE_PIX_0].pixel_clock =
		input_cfg->input_pix_clk;
	vfe_dev->axi_data.src_info[VFE_PIX_0].input_mux =
		input_cfg->d.pix_cfg.input_mux;
"""
FRESH_NEW = """	vfe_dev->axi_data.src_info[VFE_PIX_0].pixel_clock =
		input_cfg->input_pix_clk;
""" + NEW600 + """	vfe_dev->axi_data.src_info[VFE_PIX_0].input_mux =
		input_cfg->d.pix_cfg.input_mux;
"""


def main() -> None:
    t = UTIL.read_text()
    if "pixclk %ld -> 600000000" in t:
        print("vfe pixclk 600 MHz already present")
    elif OLD320 in t:
        t = t.replace(OLD320, NEW600, 1)
        print("vfe: pixclk clamp 320 -> 600 MHz")
        UTIL.write_text(t)
    elif OLD200 in t:
        t = t.replace(OLD200, NEW600, 1)
        print("vfe: pixclk clamp 200 -> 600 MHz")
        UTIL.write_text(t)
    elif FRESH_OLD in t:
        t = t.replace(FRESH_OLD, FRESH_NEW, 1)
        print("vfe: force pixclk 600 MHz")
        UTIL.write_text(t)
    else:
        raise SystemExit("msm_isp_cfg_pix pixel_clock assign not found")


if __name__ == "__main__":
    main()
