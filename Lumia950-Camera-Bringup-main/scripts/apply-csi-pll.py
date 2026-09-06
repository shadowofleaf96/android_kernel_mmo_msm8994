#!/usr/bin/env python3
"""Kernel #12: program Hill PLL to Windows MIPIDDRClock 633.6 MHz."""

from kernel_tree import kernel_tree, overlay_root
KERNEL_TREE = kernel_tree()
OVERLAY = overlay_root()

from pathlib import Path

ROOT = KERNEL_TREE
SENSOR = ROOT / "drivers/media/platform/msm/camera_v2/sensor/msm_sensor.c"
CSIPHY = ROOT / "drivers/media/platform/msm/camera_v2/sensor/csiphy/msm_csiphy.c"

PLL = r'''
static void talkman_smia_pll(struct msm_sensor_ctrl_t *s_ctrl)
{
	struct msm_camera_i2c_client *cl;
	uint16_t model = 0, pre = 0, mult = 0;
	int rc;

	if (!s_ctrl || !s_ctrl->sensor_i2c_client ||
	    !s_ctrl->sensor_i2c_client->i2c_func_tbl)
		return;
	cl = s_ctrl->sensor_i2c_client;
	rc = cl->i2c_func_tbl->i2c_read(cl, 0x0000, &model,
		MSM_CAMERA_I2C_WORD_DATA);
	if (rc < 0 || model != 0xEACA)
		return;
	/* WOA: MIPIDDRClock=633600000, 4-lane, settle 21.
	 * ext 9.6 MHz, pre=1, mult=66 → PLL 633.6 MHz.
	 * vt_sys=1 vt_pix=2 → vt 316.8 MHz. op_sys=1 → CSI 633.6 MHz.
	 */
	cl->i2c_func_tbl->i2c_write(cl, 0x0104, 1, MSM_CAMERA_I2C_BYTE_DATA);
	talkman_smia_write_w(s_ctrl, 0x0304, 1);
	talkman_smia_write_w(s_ctrl, 0x0306, 66);
	talkman_smia_write_w(s_ctrl, 0x0302, 1);
	talkman_smia_write_w(s_ctrl, 0x0300, 2);
	talkman_smia_write_w(s_ctrl, 0x0308, 1);
	talkman_smia_write_w(s_ctrl, 0x030a, 1);
	cl->i2c_func_tbl->i2c_write(cl, 0x0104, 0, MSM_CAMERA_I2C_BYTE_DATA);
	msleep(5);
	cl->i2c_func_tbl->i2c_read(cl, 0x0304, &pre, MSM_CAMERA_I2C_WORD_DATA);
	cl->i2c_func_tbl->i2c_read(cl, 0x0306, &mult, MSM_CAMERA_I2C_WORD_DATA);
	pr_err("talkman_smia pll %s pre=0x%x mult=0x%x (want 1/66)\n",
	       s_ctrl->sensordata->sensor_name, pre, mult);
}

'''


def main():
    t = SENSOR.read_text()
    if "talkman_smia_pll" not in t:
        needle = "static void talkman_smia_after_i2c(struct msm_sensor_ctrl_t *s_ctrl,"
        if needle not in t:
            raise SystemExit("after_i2c not found")
        t = t.replace(needle, PLL + needle, 1)
        print("inserted pll helper")
    else:
        print("pll helper already present")

    old = """	/* SMIA 0x0111: 0 = CSI-2, 1 = CCP2. Qualcomm CSID is CSI-2 only. */
	rc = cl->i2c_func_tbl->i2c_write(cl, 0x0111, 0,
		MSM_CAMERA_I2C_BYTE_DATA);
	if (rc)
		pr_err("talkman_smia %s CSI-2 write rc=%d\\n",
		       s_ctrl->sensordata->sensor_name, rc);

	rc = cl->i2c_func_tbl->i2c_read(cl, 0x0000, &model,
"""
    new = """	rc = cl->i2c_func_tbl->i2c_read(cl, 0x0000, &model,
"""
    if old in t:
        t = t.replace(old, new, 1)
        print("removed 0x0111 force")
    elif "CSI-2 write rc=" not in t:
        print("0x0111 force already removed")
    else:
        # try with real newline in the format string
        old2 = old.replace("\\\\n", "\\n")
        if old2 in t:
            t = t.replace(old2, new, 1)
            print("removed 0x0111 force (nl)")
        else:
            print("WARN: 0x0111 block not found")

    old = """	} else if (conf->reg_setting[0].reg_addr == 0x0103) {
		talkman_smia_dump_csi(s_ctrl);
	}
"""
    new = """	} else if (conf->reg_setting[0].reg_addr == 0x0103) {
		talkman_smia_pll(s_ctrl);
		talkman_smia_dump_csi(s_ctrl);
	}
"""
    if "talkman_smia_pll(s_ctrl);" in t:
        print("pll already hooked")
    elif old in t:
        t = t.replace(old, new, 1)
        print("hooked pll after reset")
    else:
        raise SystemExit("reset dump hook not found")

    SENSOR.write_text(t)

    c = CSIPHY.read_text()
    old = """	if (csiphy_params->settle_cnt < 0x28)
		csiphy_params->settle_cnt = 0x28;
"""
    new = """	/* WOA PHYTIMER settle = 21. */
	csiphy_params->settle_cnt = 0x15;
"""
    if "settle_cnt = 0x15" in c:
        print("settle already 0x15")
    elif old in c:
        CSIPHY.write_text(c.replace(old, new, 1))
        print("settle forced 0x15")
    else:
        raise SystemExit("settle clamp not found")
    print("apply-csi-pll done")


if __name__ == "__main__":
    main()
