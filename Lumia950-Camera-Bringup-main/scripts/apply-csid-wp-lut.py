#!/usr/bin/env python3
"""#146: WP live VF CSID CID LUT is not bullhead RAW10 0x2B.

dump-vf.log CSID0:
  +0x10 CID_LUT_VC_0 = 0x00361230  (DT CID0=0x30, CID1=0x12, CID2=0x36)
  +0x20 CID0_CFG     = 0x51        (CSI_DECODE_DPCM_10_8_10 << 4 | 1)
  +0x24 CID1_CFG     = 0x22
  +0x28 CID2_CFG     = 0x22
  +0x70 mapped long  = 0x11a       (Linux map=0)
  +0x68 irq status   = 0x2dd       (no 0x02000000 ECC)

Linux HAL still programs cid0 dt=0x2b df=2 -> cid_cfg 0x23.
Do not change TG, CAMIF, or pixclk in this flash.
"""

from kernel_tree import kernel_tree, overlay_root
KERNEL_TREE = kernel_tree()
OVERLAY = overlay_root()

from pathlib import Path

CSID = KERNEL_TREE / "drivers/media/platform/msm/camera_v2/sensor/csid/msm_csid.c"

OLD = """		val = (csid_lut_params->vc_cfg[i]->decode_format << 4) | 0x3;
		msm_camera_io_w(val, csid_dev->base +
			csid_dev->ctrl_reg->csid_reg.csid_cid_n_cfg_addr +
			(csid_lut_params->vc_cfg[i]->cid * 4));
	}
	return rc;
}
"""

NEW = """		val = (csid_lut_params->vc_cfg[i]->decode_format << 4) | 0x3;
		msm_camera_io_w(val, csid_dev->base +
			csid_dev->ctrl_reg->csid_reg.csid_cid_n_cfg_addr +
			(csid_lut_params->vc_cfg[i]->cid * 4));
	}
	/* WP VF: user-defined DT 0x30 + DPCM 10-8-10, not RAW10 0x2B. */
	msm_camera_io_w(0x00361230, csid_dev->base +
		csid_dev->ctrl_reg->csid_reg.csid_cid_lut_vc_0_addr);
	msm_camera_io_w(0x51, csid_dev->base +
		csid_dev->ctrl_reg->csid_reg.csid_cid_n_cfg_addr);
	msm_camera_io_w(0x22, csid_dev->base +
		csid_dev->ctrl_reg->csid_reg.csid_cid_n_cfg_addr + 4);
	msm_camera_io_w(0x22, csid_dev->base +
		csid_dev->ctrl_reg->csid_reg.csid_cid_n_cfg_addr + 8);
	pr_err("talkman_csid wp lut 0x%x cid0=0x%x cid1=0x%x cid2=0x%x\\n",
		msm_camera_io_r(csid_dev->base +
		csid_dev->ctrl_reg->csid_reg.csid_cid_lut_vc_0_addr),
		msm_camera_io_r(csid_dev->base +
		csid_dev->ctrl_reg->csid_reg.csid_cid_n_cfg_addr),
		msm_camera_io_r(csid_dev->base +
		csid_dev->ctrl_reg->csid_reg.csid_cid_n_cfg_addr + 4),
		msm_camera_io_r(csid_dev->base +
		csid_dev->ctrl_reg->csid_reg.csid_cid_n_cfg_addr + 8));
	return rc;
}
"""


def main() -> None:
    t = CSID.read_text()
    if "talkman_csid wp lut" in t:
        print("csid WP CID LUT already present")
        return
    if OLD not in t:
        raise SystemExit("msm_csid_cid_lut tail not found")
    CSID.write_text(t.replace(OLD, NEW, 1))
    print("csid: WP LUT 0x00361230 CID 0x51/0x22/0x22")


if __name__ == "__main__":
    main()
