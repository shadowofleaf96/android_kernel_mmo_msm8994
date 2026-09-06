#!/usr/bin/env python3
"""Kernel #17: live CSID/CSIPHY knobs + ROM-rate HS-settle.

#16 proved Hill stays 0xEACA after stream-on at ROM PLL (vt 53.1 MHz).
CSID then floods 0x500099 / 0xd00099 (lane overflow) and ISPIF never
gets PIX SOF. Windows settle 0x15 was for 633.6 MHz DDR; ROM 4-lane
RAW10 is ~66 MHz DDR (~130 ns HS-settle → 0x1A @ 200 MHz timer).

Sysfs (no reboot) after this kernel:
  echo 26 >/sys/module/msm_csiphy/parameters/settle     # 0x1A default
  echo 40 >/sys/module/msm_csiphy/parameters/settle     # 0x28
  echo 0x3210 >/sys/module/msm_csid/parameters/lane_assign
then close/reopen the camera. -1 restores DT / 0x15.
"""

from kernel_tree import kernel_tree, overlay_root
KERNEL_TREE = kernel_tree()
OVERLAY = overlay_root()

from pathlib import Path

ROOT = KERNEL_TREE
CSID = ROOT / "drivers/media/platform/msm/camera_v2/sensor/csid/msm_csid.c"
CSIPHY = ROOT / "drivers/media/platform/msm/camera_v2/sensor/csiphy/msm_csiphy.c"
SENSOR = ROOT / "drivers/media/platform/msm/camera_v2/sensor/msm_sensor.c"


def repl(path: Path, old: str, new: str, label: str) -> None:
    t = path.read_text()
    if new in t:
        print(f"{label}: already applied")
        return
    if old not in t:
        raise SystemExit(f"{label}: pattern not found in {path}")
    path.write_text(t.replace(old, new, 1))
    print(label)


def main():
    repl(
        CSID,
        "#define DBG_CSID 1\n",
        """#define DBG_CSID 1

static int talkman_lane_assign = -1;
module_param_named(lane_assign, talkman_lane_assign, int, 0644);
MODULE_PARM_DESC(lane_assign, "override CSID lane_assign (-1 = DT)");

""",
        "csid: lane_assign module_param",
    )

    repl(
        CSID,
        """	pr_err("talkman_csid id=%d lanes=%u assign=0x%x phy_sel=%u usr_clk=%u\\n",
		csid_dev->pdev->id, csid_params->lane_cnt,
		csid_params->lane_assign, csid_params->phy_sel,
		csid_params->csi_clk);
""",
        """	if (talkman_lane_assign >= 0)
		csid_params->lane_assign = talkman_lane_assign;
	pr_err("talkman_csid id=%d lanes=%u assign=0x%x phy_sel=%u usr_clk=%u override=%d\\n",
		csid_dev->pdev->id, csid_params->lane_cnt,
		csid_params->lane_assign, csid_params->phy_sel,
		csid_params->csi_clk, talkman_lane_assign);
""",
        "csid: apply lane_assign override",
    )

    repl(
        CSID,
        """		val |= 0xF;
		msm_camera_io_w(val, csidbase +
		csid_dev->ctrl_reg->csid_reg.csid_core_ctrl_1_addr);
	}

	rc = msm_csid_cid_lut(&csid_params->lut_params, csid_dev);
""",
        """		val |= 0xF;
		msm_camera_io_w(val, csidbase +
		csid_dev->ctrl_reg->csid_reg.csid_core_ctrl_1_addr);
	}
	pr_err("talkman_csid hw=0x%x ctrl0=0x%x ctrl1=0x%x\\n",
		csid_dev->hw_version,
		msm_camera_io_r(csidbase +
			csid_dev->ctrl_reg->csid_reg.csid_core_ctrl_0_addr),
		msm_camera_io_r(csidbase +
			csid_dev->ctrl_reg->csid_reg.csid_core_ctrl_1_addr));

	rc = msm_csid_cid_lut(&csid_params->lut_params, csid_dev);
""",
        "csid: dump CORE_CTRL after config",
    )

    repl(
        CSIPHY,
        """#define DBG_CSIPHY 0
""",
        """#define DBG_CSIPHY 0

static int talkman_settle = 0x1a;
module_param_named(settle, talkman_settle, int, 0644);
MODULE_PARM_DESC(settle, "CSIPHY PHYTIMER settle_cnt; -1 = leave HAL value");

""",
        "csiphy: settle module_param default 0x1A",
    )

    repl(
        CSIPHY,
        """	/* WOA PHYTIMER settle = 21. */
	csiphy_params->settle_cnt = 0x15;
""",
        """	/* #16 used Windows 0x15 (633.6 MHz DDR). ROM CSI is ~66 MHz DDR. */
	if (talkman_settle >= 0)
		csiphy_params->settle_cnt = talkman_settle;
""",
        "csiphy: settle from module_param",
    )

    repl(
        CSIPHY,
        """	pr_err("talkman_csiphy id=%d lanes=%u mask=0x%x settle=0x%x combo=%u csid=%u usr_clk=%u use=%u round=%u\\n",
		csiphy_id, csiphy_params->lane_cnt,
		csiphy_params->lane_mask, csiphy_params->settle_cnt,
		csiphy_params->combo_mode, csiphy_params->csid_core,
		csiphy_params->csiphy_clk, clk_rate, round_rate);
""",
        """	pr_err("talkman_csiphy id=%d lanes=%u mask=0x%x settle=0x%x combo=%u csid=%u usr_clk=%u use=%u round=%u hw=0x%x nm20=%d\\n",
		csiphy_id, csiphy_params->lane_cnt,
		csiphy_params->lane_mask, csiphy_params->settle_cnt,
		csiphy_params->combo_mode, csiphy_params->csid_core,
		csiphy_params->csiphy_clk, clk_rate, round_rate,
		csiphy_dev->hw_version, csiphy_dev->is_3_1_20nm_hw);
""",
        "csiphy: log hw version + 20nm flag",
    )

    repl(
        SENSOR,
        """		0x0000, 0x0100, 0x0104, 0x0110, 0x0111, 0x0112, 0x0114,
		0x0304, 0x0306, 0x034c, 0x034e, 0x0801
""",
        """		0x0000, 0x0100, 0x0104, 0x0110, 0x0111, 0x0112, 0x0114,
		0x0300, 0x0302, 0x0304, 0x0306, 0x0308, 0x030a,
		0x034c, 0x034e, 0x0800, 0x0801
""",
        "sensor: dump vt/op dividers + PHY 0x0800",
    )
    repl(
        SENSOR,
        """		dt = (regs[i] == 0x0000 || regs[i] == 0x0112 ||
		      regs[i] == 0x0304 || regs[i] == 0x0306 ||
		      regs[i] == 0x034c || regs[i] == 0x034e) ?
""",
        """		dt = (regs[i] == 0x0000 || regs[i] == 0x0112 ||
		      regs[i] == 0x0300 || regs[i] == 0x0302 ||
		      regs[i] == 0x0304 || regs[i] == 0x0306 ||
		      regs[i] == 0x0308 || regs[i] == 0x030a ||
		      regs[i] == 0x034c || regs[i] == 0x034e) ?
""",
        "sensor: WORD-width PLL divider reads",
    )

    ident = r'''
static void talkman_smia_ident(struct msm_sensor_ctrl_t *s_ctrl)
{
	struct msm_camera_i2c_client *cl;
	uint16_t mod = 0, sensor = 0, lane_cap = 0, sig_cap = 0;
	uint16_t mfr = 0, smia = 0, smiapp = 0, sensor_mfr = 0;

	if (!s_ctrl || !s_ctrl->sensor_i2c_client ||
	    !s_ctrl->sensor_i2c_client->i2c_func_tbl)
		return;
	cl = s_ctrl->sensor_i2c_client;
	/* Nokia smiapp-reg-defs.h: 0x0000 is MODULE id, 0x0016 is SENSOR id. */
	cl->i2c_func_tbl->i2c_read(cl, 0x0000, &mod, MSM_CAMERA_I2C_WORD_DATA);
	cl->i2c_func_tbl->i2c_read(cl, 0x0003, &mfr, MSM_CAMERA_I2C_BYTE_DATA);
	cl->i2c_func_tbl->i2c_read(cl, 0x0004, &smia, MSM_CAMERA_I2C_BYTE_DATA);
	cl->i2c_func_tbl->i2c_read(cl, 0x0011, &smiapp, MSM_CAMERA_I2C_BYTE_DATA);
	cl->i2c_func_tbl->i2c_read(cl, 0x0016, &sensor, MSM_CAMERA_I2C_WORD_DATA);
	cl->i2c_func_tbl->i2c_read(cl, 0x0019, &sensor_mfr,
		MSM_CAMERA_I2C_BYTE_DATA);
	cl->i2c_func_tbl->i2c_read(cl, 0x1601, &lane_cap,
		MSM_CAMERA_I2C_BYTE_DATA);
	cl->i2c_func_tbl->i2c_read(cl, 0x1602, &sig_cap,
		MSM_CAMERA_I2C_BYTE_DATA);
	pr_err("talkman_smia ident %s module=0x%04x mfr=0x%02x smia=0x%x smiapp=0x%x sensor=0x%04x sensor_mfr=0x%02x lane_cap=0x%x sig_cap=0x%x\n",
	       s_ctrl->sensordata->sensor_name, mod, mfr & 0xff, smia & 0xff,
	       smiapp & 0xff, sensor, sensor_mfr & 0xff, lane_cap & 0xff,
	       sig_cap & 0xff);
}

'''
    t = SENSOR.read_text()
    if "talkman_smia ident" in t:
        print("sensor: ident dump already present")
    else:
        needle = "static void talkman_smia_dump_csi(struct msm_sensor_ctrl_t *s_ctrl)\n"
        if needle not in t:
            raise SystemExit("dump_csi not found for ident insert")
        SENSOR.write_text(t.replace(needle, ident + needle, 1))
        print("sensor: inserted SMIA++ ident dump")
        t = SENSOR.read_text()
    if "talkman_smia_ident(s_ctrl);" in t:
        print("sensor: ident already called")
    else:
        old = """	cl = s_ctrl->sensor_i2c_client;
	for (i = 0; i < ARRAY_SIZE(regs); i++) {
"""
        new = """	cl = s_ctrl->sensor_i2c_client;
	talkman_smia_ident(s_ctrl);
	for (i = 0; i < ARRAY_SIZE(regs); i++) {
"""
        if old not in t:
            raise SystemExit("dump_csi loop not found")
        SENSOR.write_text(t.replace(old, new, 1))
        print("sensor: ident called from dump_csi")
    print("apply-csi-knobs done")


if __name__ == "__main__":
    main()
