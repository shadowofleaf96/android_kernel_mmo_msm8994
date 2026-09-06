#!/bin/bash
# Copy talkman camera overlay into an android_kernel_mmo_msm8994 checkout.
set -euo pipefail
CAM="$(cd "$(dirname "$0")/.." && pwd)"
K="${KERNEL_TREE:-$HOME/android/mmo_msm8994_talkman}"
export KERNEL_TREE="$K"
cd "$K"
echo "branch=$(git rev-parse --abbrev-ref HEAD)"
echo "KERNEL_TREE=$K"
sed -i 's/\r$//' "$CAM/dts/msm8992-talkman-camera.dtsi" "$CAM/kernel/smia65pp.c"
cp "$CAM/dts/msm8992-talkman-camera.dtsi" \
   "$K/arch/arm64/boot/dts/mmo/msm8992-talkman-camera.dtsi"
cp "$CAM/kernel/smia65pp.c" \
   "$K/drivers/media/platform/msm/camera_v2/sensor/smia65pp.c"

python3 - <<'PY'
from pathlib import Path
import os

k = Path(os.environ["KERNEL_TREE"])

p = k / "arch/arm64/boot/dts/mmo/msm8992-chi.dtsi"
t = p.read_text()
old = '#include "../qcom/msm8992-camera-sensor-mtp.dtsi"'
new = '#include "msm8992-talkman-camera.dtsi"'
if old in t:
    p.write_text(t.replace(old, new, 1))
    print("patched chi.dtsi")
elif new in t:
    print("chi.dtsi already uses talkman camera")
else:
    raise SystemExit("chi.dtsi include not found:\n" + t[:400])

p = k / "drivers/media/platform/msm/camera_v2/sensor/Makefile"
t = p.read_text()
if "smia65pp.o" not in t:
    t += "obj-$(CONFIG_SMIA65PP) += smia65pp.o\n"
    print("patched Makefile smia65pp")
else:
    print("Makefile already has smia65pp")
inc = "ccflags-y += -Idrivers/media/i2c/smiapp\n"
if inc not in t:
    t = inc + t
    print("patched Makefile smiapp include")
p.write_text(t)

p = k / "drivers/media/platform/msm/camera_v2/Kconfig"
t = p.read_text()
block = """
config SMIA65PP
	bool "SMIA++ sensors (talkman Hill/Ducati)"
	depends on MSMB_CAMERA
	---help---
	  Nokia/QCOM wrapper for SMIA++ modules (Lumia 950). Ident uses
	  mainline smiapp-reg-defs over CCI. Do not put nokia,smia on the
	  same CCI children (CCI is not an i2c_adapter).

"""
if "config SMIA65PP" not in t:
    needle = "config OV7695"
    i = t.find(needle)
    if i < 0:
        raise SystemExit("OV7695 not in Kconfig")
    p.write_text(t[:i] + block + t[i:])
    print("patched Kconfig")
else:
    print("Kconfig already has SMIA65PP")

p = k / "arch/arm64/configs/mmo_defconfig"
t = p.read_text()
if "CONFIG_SMIA65PP" not in t:
    t = t.replace("CONFIG_MSM_CAMERA_SENSOR=y\n",
                  "CONFIG_MSM_CAMERA_SENSOR=y\nCONFIG_SMIA65PP=y\n")
    print("patched mmo_defconfig SMIA65PP")
else:
    print("defconfig already has SMIA65PP")
if "CONFIG_VIDEO_SMIAPP=y" in t:
    t = t.replace("CONFIG_VIDEO_SMIAPP=y\n",
                  "# CONFIG_VIDEO_SMIAPP is not set\n")
    print("cleared mmo_defconfig VIDEO_SMIAPP")
p.write_text(t)
PY

python3 "$CAM/scripts/apply-smia-boot-safe.py"
python3 "$CAM/scripts/apply-smia-qcam-slot.py"
python3 "$CAM/scripts/apply-isp-hbi.py"
python3 "$CAM/scripts/apply-isp-cfg-stream.py"
python3 "$CAM/scripts/apply-cpp-zero-buff.py"
python3 "$CAM/scripts/apply-vfe-camif-log.py"
python3 "$CAM/scripts/apply-vfe-camif-ppl.py"
python3 "$CAM/scripts/apply-vfe-camif-1line.py"
python3 "$CAM/scripts/apply-vfe-camif-fullwin.py"
python3 "$CAM/scripts/apply-vfe-camif-st31c.py"
python3 "$CAM/scripts/apply-vfe-camif-mid.py"
python3 "$CAM/scripts/apply-vfe-pixclk.py"
python3 "$CAM/scripts/apply-vfe-camif-efs.py"
python3 "$CAM/scripts/apply-vfe-camif-epoch.py"
python3 "$CAM/scripts/apply-csid-tg-vblank.py"
python3 "$CAM/scripts/apply-vfe-camif-lastline.py"
python3 "$CAM/scripts/apply-vfe-camif-mipi.py"
python3 "$CAM/scripts/apply-vfe-camif-sync-efs.py"
python3 "$CAM/scripts/apply-vfe-axi-log.py"
python3 "$CAM/scripts/apply-vfe-camif-eof-unmask.py"
python3 "$CAM/scripts/apply-vfe-eof-dump.py"
python3 "$CAM/scripts/apply-vfe-framedrop.py"
python3 "$CAM/scripts/apply-vfe-overflow-log.py"
python3 "$CAM/scripts/apply-csi-sof.py" --phy-only
python3 "$CAM/scripts/apply-csiphy-pwr-live.py"
python3 "$CAM/scripts/apply-csiphy-settle-wp.py"
python3 "$CAM/scripts/apply-csiphy-2lane.py"
python3 "$CAM/scripts/apply-csiphy-cfg5.py"
python3 "$CAM/scripts/apply-csiphy-test-imp.py"
python3 "$CAM/scripts/apply-csiphy-wp-analog.py"
python3 "$CAM/scripts/apply-csiphy-wp-cfg2.py"
python3 "$CAM/scripts/apply-csiphy-wp-cfg3.py"
python3 "$CAM/scripts/apply-csid-ctrl1-mainline.py"
python3 "$CAM/scripts/apply-csid-tg-ones.py"
python3 "$CAM/scripts/apply-csid-tg-wp-idle.py"
python3 "$CAM/scripts/apply-csid-tg-off-after.py"
python3 "$CAM/scripts/apply-csid-tg-off-reassign.py"
python3 "$CAM/scripts/apply-vfe-camif-epoch-early.py"
python3 "$CAM/scripts/apply-vfe-sof-event-log.py"
python3 "$CAM/scripts/apply-vfe-compat-ioctl32.py"
python3 "$CAM/scripts/apply-vfe-dqevent-trace.py"
python3 "$CAM/scripts/apply-vfe-subscribe-all.py"
python3 "$CAM/scripts/apply-vfe-camif-ff0b.py"
python3 "$CAM/scripts/apply-csid-tg-ff0b.py"
python3 "$CAM/scripts/apply-csid-wp-lut.py"
python3 "$CAM/scripts/apply-csid-clk-wp.py"
python3 "$CAM/scripts/apply-cgc-wp.py"
python3 "$CAM/scripts/apply-csid-tg-restore-4080.py"
python3 "$CAM/scripts/apply-csid-tg-dt30.py"

echo DONE
git status -sb | head -20
