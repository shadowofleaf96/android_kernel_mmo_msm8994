#!/usr/bin/env python3

from kernel_tree import kernel_tree, overlay_root
KERNEL_TREE = kernel_tree()
OVERLAY = overlay_root()
from pathlib import Path

p = KERNEL_TREE / "drivers/media/platform/msm/camera_v2/sensor/msm_sensor.c"
t = p.read_text()
fn = """
static void talkman_cci_sid_scan(struct msm_sensor_ctrl_t *s_ctrl)
{
	static const uint16_t sids[] = {
		0x10, 0x20, 0x1a, 0x36, 0x37, 0x6c, 0x21, 0x30, 0x34, 0x6e
	};
	struct msm_camera_i2c_client *cl = s_ctrl->sensor_i2c_client;
	struct msm_camera_cci_client *cci;
	uint16_t saved_sid, val, i;
	int rc;

	if (!cl || !cl->cci_client || !cl->i2c_func_tbl)
		return;
	cci = cl->cci_client;
	saved_sid = cci->sid;
	pr_err("talkman_cci_scan master=%u saved_sid=0x%x\\n",
	       cci->cci_i2c_master, saved_sid);

	if (s_ctrl->sensordata &&
	    s_ctrl->sensordata->power_info.gpio_conf &&
	    s_ctrl->sensordata->power_info.gpio_conf->gpio_num_info) {
		struct msm_camera_gpio_num_info *g =
			s_ctrl->sensordata->power_info.gpio_conf->gpio_num_info;
		if (g->valid[SENSOR_GPIO_RESET])
			gpio_set_value_cansleep(
				g->gpio_num[SENSOR_GPIO_RESET], 1);
		if (g->valid[SENSOR_GPIO_STANDBY])
			gpio_set_value_cansleep(
				g->gpio_num[SENSOR_GPIO_STANDBY], 1);
		msleep(20);
	}

	for (i = 0; i < ARRAY_SIZE(sids); i++) {
		cci->sid = sids[i];
		val = 0xffff;
		rc = cl->i2c_func_tbl->i2c_read(cl, 0x0000, &val,
			MSM_CAMERA_I2C_WORD_DATA);
		pr_err("talkman_cci_scan sid=0x%02x smia0x0000 rc=%d val=0x%04x\\n",
		       sids[i], rc, val);
	}
	cci->sid = saved_sid;
}

"""
needle = "int msm_sensor_match_id(struct msm_sensor_ctrl_t *s_ctrl)"
if "talkman_cci_sid_scan" not in t:
    if needle not in t:
        raise SystemExit("match_id not found")
    t = t.replace(needle, fn + needle, 1)
old = """	if (rc < 0) {
		pr_err("%s: %s: read id failed rc %d reg 0x%x\\n",
			__func__, sensor_name, rc,
			slave_info->sensor_id_reg_addr);
		return rc;
	}
"""
new = """	if (rc < 0) {
		pr_err("%s: %s: read id failed rc %d reg 0x%x\\n",
			__func__, sensor_name, rc,
			slave_info->sensor_id_reg_addr);
		talkman_cci_sid_scan(s_ctrl);
		return rc;
	}
"""
if "talkman_cci_sid_scan(s_ctrl);" not in t:
    if old not in t:
        raise SystemExit("fail block not found")
    t = t.replace(old, new, 1)
p.write_text(t)
print("patched scan")
