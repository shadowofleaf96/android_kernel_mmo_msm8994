#!/usr/bin/env python3
"""#88 1-line CAMIF: error 0xbd40000 = 3028 lines (TG is full-height).

#87 had matching 3028-line FRAME_CFG, ppl 4088, but HAL window was still
48..4079 x 2..3025 (IMX377 dummy crop) and never EOF. Use a full window
0..ppl-1 x 0..3027 with lpf=3028.
"""

from kernel_tree import kernel_tree, overlay_root
KERNEL_TREE = kernel_tree()
OVERLAY = overlay_root()

from pathlib import Path

VFE = KERNEL_TREE / "drivers/media/platform/msm/camera_v2/isp/msm_isp44.c"


def main() -> None:
    t = VFE.read_text()
    old = """	{
		uint32_t talkman_ppl = camif_cfg->pixels_per_line;
		uint32_t talkman_lpf = 1;

		if (talkman_ppl == 4080)
			talkman_ppl = 4088;
		first_line = 0;
		last_line = 0;
		pr_err("talkman_vfe camif ppl %u -> %u lpf %u -> %u\\n",
			camif_cfg->pixels_per_line, talkman_ppl,
			camif_cfg->lines_per_frame, talkman_lpf);
		msm_camera_io_w(talkman_lpf << 16 |
			talkman_ppl, vfe_dev->vfe_base + 0x300);
	}
"""
    new = """	{
		uint32_t talkman_ppl = camif_cfg->pixels_per_line;
		uint32_t talkman_lpf = camif_cfg->lines_per_frame;

		if (talkman_ppl == 4080)
			talkman_ppl = 4088;
		first_pixel = 0;
		last_pixel = talkman_ppl - 1;
		first_line = 0;
		last_line = talkman_lpf ? talkman_lpf - 1 : 0;
		pr_err("talkman_vfe camif fullwin ppl %u -> %u lpf=%u win=%u..%u x %u..%u\\n",
			camif_cfg->pixels_per_line, talkman_ppl, talkman_lpf,
			first_pixel, last_pixel, first_line, last_line);
		msm_camera_io_w(talkman_lpf << 16 |
			talkman_ppl, vfe_dev->vfe_base + 0x300);
	}
"""
    if "talkman_vfe camif fullwin" in t or "talkman_vfe camif ff0b" in t:
        print("vfe camif full window already present")
    elif old not in t:
        raise SystemExit("vfe44 1-line override block not found")
    else:
        t = t.replace(old, new, 1)
        print("vfe44: CAMIF full window 0..ppl-1 x 0..lpf-1")
    VFE.write_text(t)


if __name__ == "__main__":
    main()
