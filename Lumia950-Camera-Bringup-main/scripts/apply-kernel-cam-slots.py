#!/usr/bin/env python3
"""Apply talkman camera slot DT + probe/logging fixes to mmo_msm8994_talkman."""

from kernel_tree import kernel_tree, overlay_root
KERNEL_TREE = kernel_tree()
OVERLAY = overlay_root()

from pathlib import Path

K = KERNEL_TREE
CAM = OVERLAY

src = (CAM / "dts/msm8992-talkman-camera.dtsi").read_bytes().replace(b"\r\n", b"\n")
(K / "arch/arm64/boot/dts/mmo/msm8992-talkman-camera.dtsi").write_bytes(src)
print("copied talkman camera dtsi")

p = K / "drivers/media/platform/msm/camera_v2/sensor/msm_sensor.c"
t = p.read_text()
old = """	if (rc < 0) {
		pr_err("%s: %s: read id failed\\n", __func__, sensor_name);
		return rc;
	}

	CDBG("%s: read id: 0x%x expected id 0x%x:\\n", __func__, chipid,
		slave_info->sensor_id);
	if (msm_sensor_id_by_mask(s_ctrl, chipid) != slave_info->sensor_id) {
		pr_err("msm_sensor_match_id chip id doesnot match\\n");
		return -ENODEV;
	}
"""
new = """	if (rc < 0) {
		pr_err("%s: %s: read id failed rc %d reg 0x%x\\n",
			__func__, sensor_name, rc,
			slave_info->sensor_id_reg_addr);
		return rc;
	}

	pr_err("%s: %s read id 0x%x expected 0x%x mask 0x%x reg 0x%x\\n",
		__func__, sensor_name, chipid, slave_info->sensor_id,
		slave_info->sensor_id_mask, slave_info->sensor_id_reg_addr);
	if (msm_sensor_id_by_mask(s_ctrl, chipid) != slave_info->sensor_id) {
		pr_err("msm_sensor_match_id chip id doesnot match\\n");
		return -ENODEV;
	}
"""
if old not in t:
    raise SystemExit("msm_sensor_match_id block not found")
p.write_text(t.replace(old, new, 1))
print("patched msm_sensor_match_id logging")

p = K / "drivers/media/platform/msm/camera_v2/sensor/msm_sensor_driver.c"
t = p.read_text()
old = """static struct platform_driver msm_sensor_platform_driver = {
	.driver = {
		.name = "qcom,camera",
		.owner = THIS_MODULE,
		.of_match_table = msm_sensor_driver_dt_match,
	},
	.remove = msm_sensor_platform_remove,
};
"""
new = """static struct platform_driver msm_sensor_platform_driver = {
	.probe = msm_sensor_driver_platform_probe,
	.driver = {
		.name = "qcom,camera",
		.owner = THIS_MODULE,
		.of_match_table = msm_sensor_driver_dt_match,
	},
	.remove = msm_sensor_platform_remove,
};
"""
if old not in t:
    raise SystemExit("platform_driver struct not found")
t = t.replace(old, new, 1)

old = """	rc = platform_driver_probe(&msm_sensor_platform_driver,
		msm_sensor_driver_platform_probe);
	if (!rc) {
		CDBG("probe success");
		return rc;
	} else {
		CDBG("probe i2c");
		rc = i2c_add_driver(&msm_sensor_driver_i2c);
	}

	return rc;
"""
new = """	rc = platform_driver_register(&msm_sensor_platform_driver);
	if (rc)
		pr_err("qcom,camera platform_driver_register rc %d\\n", rc);
	return rc;
"""
if old not in t:
    raise SystemExit("platform_driver_probe init not found")
# Forward declaration: probe is used in the driver struct before the function
# is defined. Add a prototype near the top if needed.
if "static int32_t msm_sensor_driver_platform_probe(struct platform_device *pdev);" not in t:
    needle = "static struct msm_sensor_ctrl_t *g_sctrl[MAX_CAMERAS];"
    t = t.replace(
        needle,
        needle + "\nstatic int32_t msm_sensor_driver_platform_probe("
        "struct platform_device *pdev);",
        1,
    )
p.write_text(t.replace(old, new, 1))
print("patched msm_sensor_driver to platform_driver_register")
print("DONE")
