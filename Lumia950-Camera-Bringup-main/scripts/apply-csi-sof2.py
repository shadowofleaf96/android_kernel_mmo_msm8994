#!/usr/bin/env python3
"""Kernel #11: apply grouped-hold release, longer D-PHY settle, ISPIF logs.

Kernel #10 showed the rear sensor in mode_select=1 with grouped hold still
1, CSID IRQs (likely lane/overflow bits), and userspace SOF freeze. ISPIF
SOF counts were never printed.
"""

from kernel_tree import kernel_tree, overlay_root
KERNEL_TREE = kernel_tree()
OVERLAY = overlay_root()

from pathlib import Path

ROOT = KERNEL_TREE
SENSOR = ROOT / "drivers/media/platform/msm/camera_v2/sensor/msm_sensor.c"
CSIPHY = ROOT / "drivers/media/platform/msm/camera_v2/sensor/csiphy/msm_csiphy.c"
ISPIF = ROOT / "drivers/media/platform/msm/camera_v2/ispif/msm_ispif.c"


def repl(path: Path, old: str, new: str, label: str) -> None:
    t = path.read_text()
    if new in t:
        print(f"{label}: already applied")
        return
    if old not in t:
        raise SystemExit(f"{label}: pattern not found")
    path.write_text(t.replace(old, new, 1))
    print(label)


def main():
    repl(
        SENSOR,
        """	if (want_stream) {
		mode = 0;
		rc = cl->i2c_func_tbl->i2c_read(cl, 0x0100, &mode,
			MSM_CAMERA_I2C_BYTE_DATA);
		if (rc || !(mode & 0x1)) {
			cl->i2c_func_tbl->i2c_write(cl, 0x0100, 1,
				MSM_CAMERA_I2C_BYTE_DATA);
			pr_err("talkman_smia %s forced stream-on (rc=%d val=0x%x)\\n",
			       s_ctrl->sensordata->sensor_name, rc, mode);
			msleep(10);
		}
		talkman_smia_dump_csi(s_ctrl);
""",
        """	if (want_stream) {
		/* HAL often leaves 0x0104=1; SMIA holds stream-on in shadow. */
		cl->i2c_func_tbl->i2c_write(cl, 0x0104, 0,
			MSM_CAMERA_I2C_BYTE_DATA);
		msleep(5);
		mode = 0;
		rc = cl->i2c_func_tbl->i2c_read(cl, 0x0100, &mode,
			MSM_CAMERA_I2C_BYTE_DATA);
		if (rc || !(mode & 0x1)) {
			cl->i2c_func_tbl->i2c_write(cl, 0x0100, 1,
				MSM_CAMERA_I2C_BYTE_DATA);
			pr_err("talkman_smia %s forced stream-on (rc=%d val=0x%x)\\n",
			       s_ctrl->sensordata->sensor_name, rc, mode);
			msleep(10);
		}
		talkman_smia_dump_csi(s_ctrl);
""",
        "sensor: release grouped hold on stream-on",
    )

    repl(
        CSIPHY,
        """	if (csiphy_params->settle_cnt < 8)
		csiphy_params->settle_cnt = 0x0E;
""",
        """	if (csiphy_params->settle_cnt < 0x28)
		csiphy_params->settle_cnt = 0x28;
""",
        "csiphy: settle min 0x28 (~200ns @ 200MHz)",
    )

    repl(
        ISPIF,
        """		cid_mask = msm_ispif_get_cids_mask_from_cfg(
				&params->entries[i]);
		msm_ispif_enable_intf_cids(ispif, intftype,
			cid_mask, vfe_intf, 1);
""",
        """		cid_mask = msm_ispif_get_cids_mask_from_cfg(
				&params->entries[i]);
		pr_err("talkman_ispif cfg vfe=%d intf=%d csid=%d cid_mask=0x%x crop=%d\\n",
			vfe_intf, intftype, params->entries[i].csid, cid_mask,
			params->entries[i].crop_enable);
		msm_ispif_enable_intf_cids(ispif, intftype,
			cid_mask, vfe_intf, 1);
""",
        "ispif: log cid_mask/csid/intf",
    )

    repl(
        ISPIF,
        """	if (out[vfe_id].ispifIrqStatus0 &
			ISPIF_IRQ_STATUS_PIX_SOF_MASK) {
		ispif->sof_count[vfe_id].sof_cnt[PIX0]++;
	}
	if (out[vfe_id].ispifIrqStatus0 &
			ISPIF_IRQ_STATUS_RDI0_SOF_MASK) {
		ispif->sof_count[vfe_id].sof_cnt[RDI0]++;
	}
""",
        """	if (out[vfe_id].ispifIrqStatus0 &
			ISPIF_IRQ_STATUS_PIX_SOF_MASK) {
		ispif->sof_count[vfe_id].sof_cnt[PIX0]++;
		pr_err_ratelimited("talkman_ispif PIX SOF vfe=%d n=%u st0=0x%x\\n",
			vfe_id, ispif->sof_count[vfe_id].sof_cnt[PIX0],
			out[vfe_id].ispifIrqStatus0);
	}
	if (out[vfe_id].ispifIrqStatus0 &
			ISPIF_IRQ_STATUS_RDI0_SOF_MASK) {
		ispif->sof_count[vfe_id].sof_cnt[RDI0]++;
		pr_err_ratelimited("talkman_ispif RDI0 SOF vfe=%d n=%u st0=0x%x\\n",
			vfe_id, ispif->sof_count[vfe_id].sof_cnt[RDI0],
			out[vfe_id].ispifIrqStatus0);
	}
""",
        "ispif: log PIX/RDI0 SOF",
    )
    print("apply-csi-sof2 done")


if __name__ == "__main__":
    main()
