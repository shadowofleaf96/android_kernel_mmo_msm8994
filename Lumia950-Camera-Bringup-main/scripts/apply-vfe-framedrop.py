#!/usr/bin/env python3
"""#106: keep-all on every stream. WM2 ping is 0x10000010 (unmapped) —
that is the IOMMU FAR. Encoder composite (WM2+WM3, comp 0x0C) must stay
at pattern 0. Keep-all only PIX_VIEWFINDER (WM0+WM1, ping 0x200000).
"""

from kernel_tree import kernel_tree, overlay_root
KERNEL_TREE = kernel_tree()
OVERLAY = overlay_root()

from pathlib import Path

VFE = KERNEL_TREE / "drivers/media/platform/msm/camera_v2/isp/msm_isp44.c"

OLD = """	if (!framedrop_pattern)
		framedrop_pattern = 0xFFFFFFFF;
	pr_err("talkman_vfe framedrop pat=0x%x per=%u\\n",
		framedrop_pattern, framedrop_period);
"""
NEW = """	if (!framedrop_pattern &&
	    stream_info->stream_src == PIX_VIEWFINDER)
		framedrop_pattern = 0xFFFFFFFF;
	pr_err("talkman_vfe framedrop src=%u pat=0x%x per=%u\\n",
		stream_info->stream_src, framedrop_pattern,
		framedrop_period);
"""


def main() -> None:
    t = VFE.read_text()
    if "framedrop src=%u" in t:
        print("vfe framedrop viewfinder-only already present")
        return
    if OLD not in t:
        raise SystemExit("vfe44 framedrop keep-all block not found")
    t = t.replace(OLD, NEW, 1)
    VFE.write_text(t)
    print("vfe44: framedrop keep-all PIX_VIEWFINDER only")


if __name__ == "__main__":
    main()
