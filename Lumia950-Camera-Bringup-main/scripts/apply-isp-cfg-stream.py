#!/usr/bin/env python3
"""Match bullhead VIDIOC_MSM_ISP_CFG_STREAM (36 bytes).

Talkman used stream_handle[VFE_AXI_SRC_MAX] (8) after PIX_VIDEO was added,
so sizeof is 40. Bullhead mm-qcamera-daemon encodes 36 =
uint8 + pad + MAX_NUM_STREAM(7)*uint32 + enum. STREAMON then hits
'Invalid ISP command' because the ioctl number includes the size.
"""

from kernel_tree import kernel_tree, overlay_root
KERNEL_TREE = kernel_tree()
OVERLAY = overlay_root()

from pathlib import Path

H = KERNEL_TREE / "include/media/msmb_isp.h"
U = KERNEL_TREE / "drivers/media/platform/msm/camera_v2/isp/msm_isp_util.c"

ht = H.read_text()
old = """struct msm_vfe_axi_stream_cfg_cmd {
	uint8_t num_streams;
	uint32_t stream_handle[VFE_AXI_SRC_MAX];
	enum msm_vfe_axi_stream_cmd cmd;
};
"""
new = """struct msm_vfe_axi_stream_cfg_cmd {
	uint8_t num_streams;
	/* Bullhead userspace is MAX_NUM_STREAM (7), not VFE_AXI_SRC_MAX (8). */
	uint32_t stream_handle[MAX_NUM_STREAM];
	enum msm_vfe_axi_stream_cmd cmd;
};
"""
if "stream_handle[MAX_NUM_STREAM]" in ht:
    print("cfg_cmd already MAX_NUM_STREAM")
elif old not in ht:
    raise SystemExit("axi_stream_cfg_cmd pattern not found")
else:
    H.write_text(ht.replace(old, new, 1))
    print("cfg_cmd stream_handle -> MAX_NUM_STREAM")

ut = U.read_text()
old = """	case VIDIOC_MSM_ISP_CFG_STREAM:
		mutex_lock(&vfe_dev->core_mutex);
		rc = msm_isp_cfg_axi_stream(vfe_dev, arg);
		mutex_unlock(&vfe_dev->core_mutex);
		break;
"""
new = """	case VIDIOC_MSM_ISP_CFG_STREAM: {
		struct msm_vfe_axi_stream_cfg_cmd *c = arg;

		if (c)
			pr_err("talkman_isp CFG_STREAM n=%u cmd=%u h0=0x%x\\n",
				c->num_streams, c->cmd,
				c->num_streams ? c->stream_handle[0] : 0);
		mutex_lock(&vfe_dev->core_mutex);
		rc = msm_isp_cfg_axi_stream(vfe_dev, arg);
		mutex_unlock(&vfe_dev->core_mutex);
		break;
	}
"""
if "talkman_isp CFG_STREAM" in ut:
    print("CFG_STREAM log already present")
elif old not in ut:
    raise SystemExit("CFG_STREAM case not found")
else:
    ut = ut.replace(old, new, 1)
    print("added CFG_STREAM log")

old = """		pr_err_ratelimited("%s: Invalid ISP command %d\\n", __func__,
				    cmd);
"""
new = """		pr_err_ratelimited(
			"%s: Invalid ISP command %d nr=%u size=%u\\n",
			__func__, cmd, _IOC_NR(cmd), _IOC_SIZE(cmd));
"""
if "_IOC_SIZE(cmd)" in ut:
    print("invalid-cmd size log already present")
elif old not in ut:
    raise SystemExit("Invalid ISP command pattern not found")
else:
    ut = ut.replace(old, new, 1)
    print("added ioctl nr/size to invalid-cmd log")

U.write_text(ut)
print("apply-isp-cfg-stream done")
