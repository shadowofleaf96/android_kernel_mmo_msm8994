#!/usr/bin/env python3
"""Let CFG_SINIT_PROBE find the already-registered smia65pp sensor.

Bullhead mm-qcamera-daemon always ioctl CFG_SINIT_PROBE. That looks up
g_sctrl[camera_id], which only qcom,camera slots fill. Our Hill node is
qcom,smia65pp (msm_sensor_platform_probe), so probe returned -22 even
after libmmcamera_imx230.so loaded.

Do not add qcom,camera on the same CCI/GPIOs. After delayed ident, put
the smia65pp s_ctrl into g_sctrl with is_probe_succeed=1 so the daemon
takes the already-probed shortcut (no power_up at probe).
"""

from kernel_tree import kernel_tree, overlay_root
KERNEL_TREE = kernel_tree()
OVERLAY = overlay_root()

from pathlib import Path

K = KERNEL_TREE
DRV = K / "drivers/media/platform/msm/camera_v2/sensor/msm_sensor_driver.c"
HDR = K / "drivers/media/platform/msm/camera_v2/sensor/msm_sensor.h"

BIND_FN = r"""
int msm_sensor_driver_bind_probed(struct msm_sensor_ctrl_t *s_ctrl,
				  uint16_t sensor_id)
{
	struct msm_camera_sensor_slave_info *cam;

	if (!s_ctrl || !s_ctrl->sensordata)
		return -EINVAL;
	if (s_ctrl->id >= MAX_CAMERAS) {
		pr_err("talkman_smia: bind slot id %u out of range\n",
		       s_ctrl->id);
		return -EINVAL;
	}
	if (g_sctrl[s_ctrl->id] && g_sctrl[s_ctrl->id] != s_ctrl) {
		pr_err("talkman_smia: g_sctrl[%u] already taken\n", s_ctrl->id);
		return -EBUSY;
	}

	cam = s_ctrl->sensordata->cam_slave_info;
	if (!cam) {
		cam = kzalloc(sizeof(*cam), GFP_KERNEL);
		if (!cam)
			return -ENOMEM;
		s_ctrl->sensordata->cam_slave_info = cam;
	}
	if (s_ctrl->sensordata->sensor_name)
		strlcpy(cam->sensor_name, s_ctrl->sensordata->sensor_name,
			sizeof(cam->sensor_name));
	cam->sensor_id_info.sensor_id = sensor_id;
	s_ctrl->is_probe_succeed = 1;
	g_sctrl[s_ctrl->id] = s_ctrl;
	pr_err("talkman_smia: g_sctrl[%u]=%s id=0x%04x (CFG_SINIT_PROBE slot)\n",
	       s_ctrl->id, cam->sensor_name, sensor_id);
	return 0;
}
EXPORT_SYMBOL(msm_sensor_driver_bind_probed);

"""

DECL = """
int msm_sensor_driver_bind_probed(struct msm_sensor_ctrl_t *s_ctrl,
	uint16_t sensor_id);
"""


def main() -> None:
    t = DRV.read_text()
    if "msm_sensor_driver_bind_probed" in t:
        print("msm_sensor_driver.c already has bind_probed")
    else:
        needle = "static struct msm_sensor_ctrl_t *g_sctrl[MAX_CAMERAS];\n"
        if needle not in t:
            raise SystemExit("g_sctrl declaration not found")
        t = t.replace(needle, needle + BIND_FN, 1)
        DRV.write_text(t)
        print("added msm_sensor_driver_bind_probed")

    h = HDR.read_text()
    if "msm_sensor_driver_bind_probed" in h:
        print("msm_sensor.h already has bind_probed")
    else:
        needle = "int32_t msm_sensor_platform_probe(struct platform_device *pdev,\n	const void *data);\n"
        if needle not in h:
            raise SystemExit("platform_probe decl not found")
        HDR.write_text(h.replace(needle, needle + DECL, 1))
        print("declared msm_sensor_driver_bind_probed")


if __name__ == "__main__":
    main()
