#!/usr/bin/env python3
"""Match bullhead mm-qcamera-daemon VIDIOC_MSM_ISP_INPUT_CFG (148 bytes)."""

from kernel_tree import kernel_tree, overlay_root
KERNEL_TREE = kernel_tree()
OVERLAY = overlay_root()

from pathlib import Path

p = KERNEL_TREE / "include/media/msmb_isp.h"
t = p.read_text()
old = """	uint32_t epoch_line0;
	uint32_t epoch_line1;
	enum msm_vfe_camif_input camif_input;
"""
new = """	uint32_t epoch_line0;
	uint32_t epoch_line1;
	uint32_t hbi_cnt;
	enum msm_vfe_camif_input camif_input;
"""
if "uint32_t hbi_cnt;" in t:
    print("hbi_cnt already present")
elif old not in t:
    raise SystemExit("camif_cfg pattern not found")
else:
    p.write_text(t.replace(old, new, 1))
    print("added hbi_cnt")
