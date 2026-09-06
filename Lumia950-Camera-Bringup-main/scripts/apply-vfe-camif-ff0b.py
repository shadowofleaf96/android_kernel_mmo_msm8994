#!/usr/bin/env python3
"""#144: WP live VF CAMIF is 2496x1872 window 0..2495 x 0..1871.

Bullhead HAL still programs 4080x3028. Sensor DCC FF0B is already 2496x1872.
Do not change pixclk, 0x2E8, 0x2F8, or CGC in this flash.
"""

from kernel_tree import kernel_tree, overlay_root
KERNEL_TREE = kernel_tree()
OVERLAY = overlay_root()

from pathlib import Path

VFE = KERNEL_TREE / "drivers/media/platform/msm/camera_v2/isp/msm_isp44.c"

OLD = """		if (talkman_ppl == 4080)
			talkman_ppl = 4088;
		first_pixel = 0;
		last_pixel = talkman_ppl - 1;
		first_line = 0;
		last_line = talkman_lpf > 1 ? talkman_lpf - 2 : 0;
		pr_err("talkman_vfe camif fullwin ppl %u -> %u lpf=%u win=%u..%u x %u..%u\\n",
"""

NEW = """		if (talkman_ppl == 4080) {
			talkman_ppl = 2496;
			talkman_lpf = 1872;
		}
		first_pixel = 0;
		last_pixel = talkman_ppl - 1;
		first_line = 0;
		last_line = talkman_lpf ? talkman_lpf - 1 : 0;
		pr_err("talkman_vfe camif ff0b ppl %u -> %u lpf=%u win=%u..%u x %u..%u\\n",
"""


def main() -> None:
    t = VFE.read_text()
    if "talkman_vfe camif ff0b" in t:
        print("vfe camif ff0b 2496x1872 already present")
        return
    if OLD not in t:
        raise SystemExit("vfe44 fullwin 4080->4088 block not found")
    VFE.write_text(t.replace(OLD, NEW, 1))
    print("vfe44: CAMIF 4080x3028 -> WP VF 2496x1872 full window")


if __name__ == "__main__":
    main()
