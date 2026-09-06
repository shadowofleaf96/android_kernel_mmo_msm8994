#!/usr/bin/env python3
"""#86 CAMIF_STATUS 0xff8 with SOF and no EOF.

Qualcomm CAMIF error status is (lines << 16) | pixels of the frame that
failed. 0x00000ff8 => 0 lines, 4088 pixels: overflow on line 0, 8 pixels
past HAL pixels_per_line=4080. Force FRAME_CFG ppl to 4088; keep the
window 48..4079.
"""

from kernel_tree import kernel_tree, overlay_root
KERNEL_TREE = kernel_tree()
OVERLAY = overlay_root()

from pathlib import Path

VFE = KERNEL_TREE / "drivers/media/platform/msm/camera_v2/isp/msm_isp44.c"


def main() -> None:
    t = VFE.read_text()
    old = """	msm_camera_io_w(camif_cfg->lines_per_frame << 16 |
		camif_cfg->pixels_per_line, vfe_dev->vfe_base + 0x300);
"""
    new = """	{
		uint32_t talkman_ppl = camif_cfg->pixels_per_line;

		if (talkman_ppl == 4080)
			talkman_ppl = 4088;
		pr_err("talkman_vfe camif ppl %u -> %u\\n",
			camif_cfg->pixels_per_line, talkman_ppl);
		msm_camera_io_w(camif_cfg->lines_per_frame << 16 |
			talkman_ppl, vfe_dev->vfe_base + 0x300);
	}
"""
    if ("talkman_vfe camif fullwin" in t or "talkman_vfe camif ppl" in t
            or "talkman_vfe camif ff0b" in t):
        print("vfe camif ppl override already present")
        return
    elif old not in t:
        raise SystemExit("vfe44 FRAME_CFG ppl write not found")
    else:
        t = t.replace(old, new, 1)
        print("vfe44: FRAME_CFG ppl 4080->4088")
    VFE.write_text(t)


if __name__ == "__main__":
    main()
