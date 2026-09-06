#!/usr/bin/env python3
"""#87: ppl 4088 cleared CAMIF overflow, but EOF still never fires.

SOF lockstep at 37 fps with only line-0 overflow before the ppl fix
means CAMIF may see ~1 line per SOF. Force FRAME_CFG lines=1 and
window last_line=0 so a single complete line can generate EOF.
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

		if (talkman_ppl == 4080)
			talkman_ppl = 4088;
		pr_err("talkman_vfe camif ppl %u -> %u\\n",
			camif_cfg->pixels_per_line, talkman_ppl);
		msm_camera_io_w(camif_cfg->lines_per_frame << 16 |
			talkman_ppl, vfe_dev->vfe_base + 0x300);
	}
"""
    new = """	{
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
    if "talkman_vfe camif fullwin" in t or "talkman_vfe camif ff0b" in t:
        print("vfe camif 1-line skipped (full window is the current override)")
        return
    if "talkman_vfe camif ppl" in t and "lpf %u" in t:
        print("vfe camif 1-line override already present")
        return
    elif old not in t:
        raise SystemExit("vfe44 ppl override block not found")
    else:
        t = t.replace(old, new, 1)
        print("vfe44: CAMIF 1-line frame/window")
    VFE.write_text(t)


if __name__ == "__main__":
    main()
