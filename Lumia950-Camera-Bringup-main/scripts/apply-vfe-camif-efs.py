#!/usr/bin/env python3
"""#94: 600 MHz no overflow, CAMIF SOF+EPOCH0, never EOF.

V40_CAMIF_OFF=0x2F8, V40_CAMIF_LEN=36. Next word 0x2FC is CAMIF_EFS
(vfe8x_proc.h VFE_CAMIFConfigType / vfe_cmds_camif_efs):
  efsEndOfLine:8 | efsStartOfLine:8 | efsEndOfFrame:8 | efsStartOfFrame:8
CAF msm_isp44.c never writes it (live dump was 0). v1 memcpy'd the whole
blob from HAL. QCOM IFE clock guide min HBI=64, min VBI=32.
"""

from kernel_tree import kernel_tree, overlay_root
KERNEL_TREE = kernel_tree()
OVERLAY = overlay_root()

from pathlib import Path

VFE = KERNEL_TREE / "drivers/media/platform/msm/camera_v2/isp/msm_isp44.c"

NEEDLE = """	pr_err("talkman_vfe camif clk=%ld mux=%u pat=%u in=%u %ux%u win=%u..%u x %u..%u hbi=%u\\n",
		vfe_dev->axi_data.src_info[VFE_PIX_0].pixel_clock,
		pix_cfg->input_mux, pix_cfg->pixel_pattern,
		camif_cfg->camif_input,
		camif_cfg->pixels_per_line, camif_cfg->lines_per_frame,
		first_pixel, last_pixel, first_line, last_line,
		camif_cfg->hbi_cnt);
"""
INSERT = NEEDLE + """	/* V40 CAMIF blob: 0x2FC = EFS. CAF v2 left it 0. */
	msm_camera_io_w(0x00200040, vfe_dev->vfe_base + 0x2FC);
	pr_err("talkman_vfe camif efs 0x2fc=0x00200040 (eol=64 eof=32)\\n");
"""


def main() -> None:
    t = VFE.read_text()
    if "talkman_vfe camif efs 0x2fc=" in t:
        print("vfe camif EFS already present")
        return
    if NEEDLE not in t:
        raise SystemExit("vfe44 camif clk log not found")
    t = t.replace(NEEDLE, INSERT, 1)
    VFE.write_text(t)
    print("vfe44: CAMIF EFS 0x2FC = 0x00200040")


if __name__ == "__main__":
    main()
