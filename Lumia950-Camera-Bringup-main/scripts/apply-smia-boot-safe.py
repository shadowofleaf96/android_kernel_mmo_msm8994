#!/usr/bin/env python3
"""Boot-safe named-sensor probe (talkman smia65pp).

1) DT pdevs have id_entry == NULL; CDBG is pr_debug and still evaluates
   pdev->id_entry->name → panic. Kernel #1 bootloop.

2) msm_sensor_platform_probe power_up() + power_down() at *kernel init*.
   That is the Nokia TWRP ID path. On talkman Android it reboots the
   board (shared LVS1 and/or qcamera daemon racing the same CCI/GPIOs).
   Kernels #2/#3 still bootlooped after the id_entry fix.

   qcamera (mm-qcamera-daemon) is supposed to power the MSM sensor on
   first open, like qcom,camera slots. SMIA++ match_id still runs then
   via smia65pp_match_id. Hill only: one static s_ctrl (two nodes crash,
   as snaccy saw).

   Kernel #4 still bootlooped after skipping power_up/down: this function
   still does get_dt_data + camera_init_v4l2 + msm_sd_register. Keep these
   patches, but smia65pp must not call msm_sensor_platform_probe until a
   no-op CCI bind has booted (smia-msm#5).
"""

from kernel_tree import kernel_tree, overlay_root
KERNEL_TREE = kernel_tree()
OVERLAY = overlay_root()

from pathlib import Path

P = KERNEL_TREE / "drivers/media/platform/msm/camera_v2/sensor/msm_sensor.c"
t = P.read_text()

old_id = """	s_ctrl->pdev = pdev;
	CDBG("%s called data %pK\\n", __func__, data);
	CDBG("%s pdev name %s\\n", __func__, pdev->id_entry->name);
	if (pdev->dev.of_node) {
"""
new_id = """	s_ctrl->pdev = pdev;
	CDBG("%s called data %pK\\n", __func__, data);
	/* DT pdevs have id_entry == NULL; pr_debug still evaluates args. */
	pr_err("%s: %s\\n", __func__, dev_name(&pdev->dev));
	if (!msm_cci_get_subdev()) {
		pr_err("%s: CCI not ready, deferring %s\\n",
			__func__, dev_name(&pdev->dev));
		return -EPROBE_DEFER;
	}
	if (pdev->dev.of_node) {
"""
if new_id in t:
    print("id_entry/CCI defer already applied")
elif old_id not in t:
    raise SystemExit("id_entry CDBG block not found")
else:
    t = t.replace(old_id, new_id, 1)
    print("patched id_entry NULL + CCI defer")

old_pu = """	rc = s_ctrl->func_tbl->sensor_power_up(s_ctrl);
	if (rc < 0) {
		pr_err("%s %s power up failed\\n", __func__,
			s_ctrl->sensordata->sensor_name);
		kfree(s_ctrl->sensordata->power_info.clk_info);
		kfree(cci_client);
		return rc;
	}

	pr_info("%s %s probe succeeded\\n", __func__,
		s_ctrl->sensordata->sensor_name);
"""
new_pu = """	/* Do not power_up at boot. qcamera will s_power() later.
	 * Boot-time power_up/down reboots talkman (kernels smia-msm #1-#3).
	 */
	pr_err("%s %s probe register-only (SMIA++ power deferred to qcamera)\\n",
		__func__, s_ctrl->sensordata->sensor_name);
"""
if new_pu in t:
    print("boot power_up skip already applied")
elif old_pu not in t:
    raise SystemExit("sensor_power_up block not found")
else:
    t = t.replace(old_pu, new_pu, 1)
    print("patched skip boot power_up")

old_pd = """	s_ctrl->msm_sd.sd.devnode->fops =
		&msm_sensor_v4l2_subdev_fops;

	CDBG("%s:%d\\n", __func__, __LINE__);

	s_ctrl->func_tbl->sensor_power_down(s_ctrl);
	CDBG("%s:%d\\n", __func__, __LINE__);
	return rc;
"""
new_pd = """	if (s_ctrl->msm_sd.sd.devnode)
		s_ctrl->msm_sd.sd.devnode->fops =
			&msm_sensor_v4l2_subdev_fops;

	pr_err("%s:%d registered without boot power_up/down\\n",
		__func__, __LINE__);
	return rc;
"""
if new_pd in t:
    print("boot power_down skip already applied")
elif old_pd not in t:
    raise SystemExit("sensor_power_down/devnode block not found")
else:
    t = t.replace(old_pd, new_pd, 1)
    print("patched skip boot power_down + NULL-safe devnode")

# Nokia smia65pp copied msm_sensor_config only. This tree's ov5645/ov7695
# also set sensor_config32 (32-bit qcamera on arm64). Export the generic
# helper so smia65pp can match that func_tbl without duplicating ov* YUV
# tables.
old_c32 = "static int msm_sensor_config32(struct msm_sensor_ctrl_t *s_ctrl,\n\tvoid __user *argp)"
new_c32 = "int msm_sensor_config32(struct msm_sensor_ctrl_t *s_ctrl,\n\tvoid __user *argp)"
if t.find("static int msm_sensor_config32(") >= 0:
    t = t.replace(old_c32, new_c32, 1)
    print("exported msm_sensor_config32")
elif "int msm_sensor_config32(" in t:
    print("msm_sensor_config32 already exported")
else:
    raise SystemExit("msm_sensor_config32 not found")

P.write_text(t)

H = KERNEL_TREE / "drivers/media/platform/msm/camera_v2/sensor/msm_sensor.h"
h = H.read_text()
decl = """
#ifdef CONFIG_COMPAT
int msm_sensor_config32(struct msm_sensor_ctrl_t *s_ctrl, void __user *argp);
#endif
"""
if "int msm_sensor_config32(" in h:
    print("msm_sensor.h already has config32")
else:
    needle = "int msm_sensor_config(struct msm_sensor_ctrl_t *s_ctrl, void __user *argp);\n"
    if needle not in h:
        raise SystemExit("msm_sensor_config decl not found")
    H.write_text(h.replace(needle, needle + decl, 1))
    print("declared msm_sensor_config32 in msm_sensor.h")

print("apply-smia-boot-safe done")
