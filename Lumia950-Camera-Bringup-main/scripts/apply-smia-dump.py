#!/usr/bin/env python3
"""Dump SMIA++ ID / window / CSI / capability regs after a successful match_id."""

from kernel_tree import kernel_tree, overlay_root
KERNEL_TREE = kernel_tree()
OVERLAY = overlay_root()

from pathlib import Path

p = KERNEL_TREE / "drivers/media/platform/msm/camera_v2/sensor/msm_sensor.c"
t = p.read_text()
fn = r"""
static void talkman_smia_dump(struct msm_sensor_ctrl_t *s_ctrl)
{
	static const uint16_t regs[] = {
		0x0000, 0x0002, 0x0004, 0x0006, 0x000c, 0x0011,
		0x0112, 0x0114, 0x0136, 0x0202, 0x0204,
		0x0300, 0x0302, 0x0304, 0x0306, 0x0308, 0x030a,
		0x0340, 0x0342, 0x0344, 0x0346, 0x0348, 0x034a,
		0x034c, 0x034e, 0x0380, 0x0382, 0x0384, 0x0386,
		0x0900, 0x1180, 0x1182, 0x1184, 0x1186,
		0x1188, 0x118a, 0x118c, 0x118e, 0x1601
	};
	struct msm_camera_i2c_client *cl = s_ctrl->sensor_i2c_client;
	uint16_t val, i;
	int rc;

	if (!cl || !cl->i2c_func_tbl)
		return;
	for (i = 0; i < ARRAY_SIZE(regs); i++) {
		val = 0xffff;
		rc = cl->i2c_func_tbl->i2c_read(cl, regs[i], &val,
			MSM_CAMERA_I2C_WORD_DATA);
		pr_err("talkman_smia %s reg 0x%04x rc=%d val=0x%04x\n",
		       s_ctrl->sensordata->sensor_name, regs[i], rc, val);
	}
}

"""
if "talkman_smia_dump" in t:
    print("smia dump already present")
else:
    needle = "int msm_sensor_match_id(struct msm_sensor_ctrl_t *s_ctrl)"
    if needle not in t:
        raise SystemExit("match_id not found")
    t = t.replace(needle, fn + needle, 1)
    old = """	if (msm_sensor_id_by_mask(s_ctrl, chipid) != slave_info->sensor_id) {
		pr_err("msm_sensor_match_id chip id doesnot match\\n");
		return -ENODEV;
	}
	return rc;
"""
    new = """	if (msm_sensor_id_by_mask(s_ctrl, chipid) != slave_info->sensor_id) {
		pr_err("msm_sensor_match_id chip id doesnot match\\n");
		return -ENODEV;
	}
	talkman_smia_dump(s_ctrl);
	return rc;
"""
    if old not in t:
        raise SystemExit("success return not found")
    t = t.replace(old, new, 1)
    p.write_text(t)
    print("patched smia dump")
