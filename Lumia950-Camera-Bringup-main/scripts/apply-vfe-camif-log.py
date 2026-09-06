#!/usr/bin/env python3
"""Log VFE44 CAMIF window/pixclk and SOF/EOF. Talkman is qcom,vfe44.

#85 already dumped CAMIF regs on error: FRAME 4080x3028, window 48..4079 x
2..3025, status 0xff8. Need pixclk/pattern/input and whether CAMIF SOF fires.
"""

from kernel_tree import kernel_tree, overlay_root
KERNEL_TREE = kernel_tree()
OVERLAY = overlay_root()

from pathlib import Path

VFE = KERNEL_TREE / "drivers/media/platform/msm/camera_v2/isp/msm_isp44.c"


def main() -> None:
    t = VFE.read_text()
    old_cfg = """	msm_camera_io_w(first_line << 16 | last_line,
	vfe_dev->vfe_base + 0x308);
"""
    new_cfg = """	msm_camera_io_w(first_line << 16 | last_line,
	vfe_dev->vfe_base + 0x308);
	pr_err("talkman_vfe camif clk=%ld mux=%u pat=%u in=%u %ux%u win=%u..%u x %u..%u hbi=%u\\n",
		vfe_dev->axi_data.src_info[VFE_PIX_0].pixel_clock,
		pix_cfg->input_mux, pix_cfg->pixel_pattern,
		camif_cfg->camif_input,
		camif_cfg->pixels_per_line, camif_cfg->lines_per_frame,
		first_pixel, last_pixel, first_line, last_line,
		camif_cfg->hbi_cnt);
"""
    if "talkman_vfe camif clk=" in t:
        print("vfe camif cfg log already present")
    elif old_cfg not in t:
        raise SystemExit("vfe44 cfg_camif window write not found")
    else:
        t = t.replace(old_cfg, new_cfg, 1)
        print("vfe44: CAMIF cfg log")

    old_irq = """	if (irq_status0 & 0x1)
		vfe_dev->axi_data.src_info[VFE_PIX_0].camif_sof_frame_id++;
"""
    new_irq = """	if (irq_status0 & 0x1)
		vfe_dev->axi_data.src_info[VFE_PIX_0].camif_sof_frame_id++;
	if (irq_status0 & 0x3) {
		static int talkman_vfe_camif_irq;

		if (talkman_vfe_camif_irq < 8) {
			talkman_vfe_camif_irq++;
			pr_err("talkman_vfe camif irq n=%d s0=0x%x sof=%d eof=%d fid=%u\\n",
				talkman_vfe_camif_irq, irq_status0,
				!!(irq_status0 & 1), !!(irq_status0 & 2),
				vfe_dev->axi_data.src_info[VFE_PIX_0].
					camif_sof_frame_id);
		}
	}
"""
    if "talkman_vfe camif irq n=" in t:
        print("vfe camif irq log already present")
    elif old_irq not in t:
        raise SystemExit("vfe44 CAMIF SOF frame_id increment not found")
    else:
        t = t.replace(old_irq, new_irq, 1)
        print("vfe44: CAMIF SOF/EOF log")

    old_err = """		pr_err("%s: camif error status: 0x%x\\n",
			__func__, vfe_dev->error_info.camif_status);
		msm_camera_io_dump_2(vfe_dev->vfe_base + 0x2f4, 0x30);
"""
    new_err = """		pr_err("%s: camif error status: 0x%x\\n",
			__func__, vfe_dev->error_info.camif_status);
		pr_err("talkman_vfe camif err cfg1c=0x%x in2e8=0x%x st=0x%x\\n",
			msm_camera_io_r(vfe_dev->vfe_base + 0x1C),
			msm_camera_io_r(vfe_dev->vfe_base + 0x2E8),
			vfe_dev->error_info.camif_status);
		msm_camera_io_dump_2(vfe_dev->vfe_base + 0x2f4, 0x30);
"""
    if "talkman_vfe camif err cfg1c=" in t:
        print("vfe camif err extra dump already present")
    elif old_err not in t:
        raise SystemExit("vfe44 camif error dump not found")
    else:
        t = t.replace(old_err, new_err, 1)
        print("vfe44: CAMIF error mux/input dump")

    VFE.write_text(t)
    print("apply-vfe-camif-log done")


if __name__ == "__main__":
    main()
