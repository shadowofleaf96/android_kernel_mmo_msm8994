#!/usr/bin/env python3
"""After each SMIA I2C table write, crop Hill (0xEACA) to a VFE-safe window.

MSM8992 VFE was brought up on IMX377 4080x3028. The Sharp rear defaults
to 5344x4016, which hangs the SoC (watchdog, no Oops).
"""

from kernel_tree import kernel_tree, overlay_root
KERNEL_TREE = kernel_tree()
OVERLAY = overlay_root()

from pathlib import Path

P = KERNEL_TREE / "drivers/media/platform/msm/camera_v2/sensor/msm_sensor.c"
t = P.read_text()

crop_fn = r'''
static int talkman_smia_write_w(struct msm_sensor_ctrl_t *s_ctrl,
	uint16_t addr, uint16_t val)
{
	return s_ctrl->sensor_i2c_client->i2c_func_tbl->i2c_write(
		s_ctrl->sensor_i2c_client, addr, val,
		MSM_CAMERA_I2C_WORD_DATA);
}

static void talkman_smia_vfe_crop(struct msm_sensor_ctrl_t *s_ctrl)
{
	struct msm_camera_i2c_client *cl;
	uint16_t model = 0, out_w = 0, out_h = 0;
	const uint16_t crop_w = 4080, crop_h = 3028;
	uint16_t x0, y0, x1, y1;
	int rc;

	if (!s_ctrl || !s_ctrl->sensor_i2c_client ||
	    !s_ctrl->sensor_i2c_client->i2c_func_tbl)
		return;
	cl = s_ctrl->sensor_i2c_client;
	rc = cl->i2c_func_tbl->i2c_read(cl, 0x0000, &model,
		MSM_CAMERA_I2C_WORD_DATA);
	if (rc < 0)
		return;
	/* Rear Sharp 20MP only. Front 2600-wide is already VFE-safe. */
	if (model != 0xEACA)
		return;
	rc = cl->i2c_func_tbl->i2c_read(cl, 0x034c, &out_w,
		MSM_CAMERA_I2C_WORD_DATA);
	rc |= cl->i2c_func_tbl->i2c_read(cl, 0x034e, &out_h,
		MSM_CAMERA_I2C_WORD_DATA);
	if (rc < 0)
		return;
	if (out_w <= crop_w && out_h <= crop_h)
		return;
	x0 = (out_w - crop_w) / 2;
	y0 = (out_h - crop_h) / 2;
	x0 &= ~1;
	y0 &= ~1;
	x1 = x0 + crop_w - 1;
	y1 = y0 + crop_h - 1;
	/* Grouped parameter hold so the window takes effect together. */
	cl->i2c_func_tbl->i2c_write(cl, 0x0104, 1, MSM_CAMERA_I2C_BYTE_DATA);
	talkman_smia_write_w(s_ctrl, 0x0344, x0);
	talkman_smia_write_w(s_ctrl, 0x0346, y0);
	talkman_smia_write_w(s_ctrl, 0x0348, x1);
	talkman_smia_write_w(s_ctrl, 0x034a, y1);
	talkman_smia_write_w(s_ctrl, 0x034c, crop_w);
	talkman_smia_write_w(s_ctrl, 0x034e, crop_h);
	cl->i2c_func_tbl->i2c_write(cl, 0x0104, 0, MSM_CAMERA_I2C_BYTE_DATA);
	pr_err("talkman_smia crop %s %ux%u -> %ux%u origin %u,%u\n",
	       s_ctrl->sensordata->sensor_name, out_w, out_h,
	       crop_w, crop_h, x0, y0);
}

'''

if "talkman_smia_vfe_crop" in t:
    print("vfe crop already present")
else:
    needle = "static void talkman_smia_dump(struct msm_sensor_ctrl_t *s_ctrl)"
    if needle not in t:
        # dump helper may sit above match_id; insert before msm_sensor_config
        needle = "int msm_sensor_config(struct msm_sensor_ctrl_t *s_ctrl, void __user *argp)"
        if needle not in t:
            raise SystemExit("no insert point for crop helper")
        t = t.replace(needle, crop_fn + needle, 1)
        print("inserted crop helper before msm_sensor_config")
    else:
        t = t.replace(needle, crop_fn + needle, 1)
        print("inserted crop helper before dump")

old32 = """		rc = s_ctrl->sensor_i2c_client->i2c_func_tbl->
			i2c_write_table(s_ctrl->sensor_i2c_client,
			&conf_array);
		kfree(reg_setting);
		break;
	}
	case CFG_SLAVE_READ_I2C: {
		struct msm_camera_i2c_read_config read_config;
		struct msm_camera_i2c_read_config *read_config_ptr = NULL;
"""
new32 = """		rc = s_ctrl->sensor_i2c_client->i2c_func_tbl->
			i2c_write_table(s_ctrl->sensor_i2c_client,
			&conf_array);
		if (!rc)
			talkman_smia_vfe_crop(s_ctrl);
		kfree(reg_setting);
		break;
	}
	case CFG_SLAVE_READ_I2C: {
		struct msm_camera_i2c_read_config read_config;
		struct msm_camera_i2c_read_config *read_config_ptr = NULL;
"""
old64 = """		rc = s_ctrl->sensor_i2c_client->i2c_func_tbl->i2c_write_table(
			s_ctrl->sensor_i2c_client, &conf_array);
		kfree(reg_setting);
		break;
	}
	case CFG_SLAVE_READ_I2C: {
		struct msm_camera_i2c_read_config read_config;
"""
new64 = """		rc = s_ctrl->sensor_i2c_client->i2c_func_tbl->i2c_write_table(
			s_ctrl->sensor_i2c_client, &conf_array);
		if (!rc)
			talkman_smia_vfe_crop(s_ctrl);
		kfree(reg_setting);
		break;
	}
	case CFG_SLAVE_READ_I2C: {
		struct msm_camera_i2c_read_config read_config;
"""

n = 0
if old32 in t:
    t = t.replace(old32, new32, 1)
    n += 1
    print("hooked config32 WRITE_I2C_ARRAY")
else:
    if "talkman_smia_vfe_crop(s_ctrl)" in t:
        print("config32 hook already present")
    else:
        raise SystemExit("config32 WRITE_I2C_ARRAY pattern not found")

if old64 in t:
    t = t.replace(old64, new64, 1)
    n += 1
    print("hooked config WRITE_I2C_ARRAY")
elif t.count("talkman_smia_vfe_crop(s_ctrl)") >= 2:
    print("config hook already present")
else:
    raise SystemExit("config WRITE_I2C_ARRAY pattern not found")

P.write_text(t)
print("apply-smia-vfe-crop done")
