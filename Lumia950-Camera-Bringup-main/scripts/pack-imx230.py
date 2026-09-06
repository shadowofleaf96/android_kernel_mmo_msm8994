#!/usr/bin/env python3
"""Ship libmmcamera_imx230.so so qcamera can dlopen the Hill subdev name.

Kernel #15 registers the MSM sensor as imx230. Bullhead userspace only has
libmmcamera_imx377.so, so sensor_probe fails before any I2C. This is the
bullhead sensor-lib ABI (same .so layout) with:
  - filename / SONAME / sensor_name = imx230
  - SMIA++ I2C + Hill window from smia9
  - chromatix names still imx377_* (those blobs exist on the ROM)

Not a Sony IMX230 CAF lib. Identity is imx230; tables stay SMIA-patched.
"""
from __future__ import annotations

import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "out"
MOD = OUT / "magisk-talkman-smia"
LIBDIR = MOD / "system" / "vendor" / "lib"

SENSOR_NAME_OFF = 0x3008
SONAME = b"libmmcamera_imx377.so"
SONAME_NEW = b"libmmcamera_imx230.so"

PFSD = b"""#!/system/bin/sh
# Magisk overlay of /vendor is skipped on this 3.10 tree.
# Copy (do not bind from /sdcard: noexec + sdcardfs blocks dlopen).
MODDIR=${0%/*}
log=/data/local/tmp/talkman-smia.log
echo "pfsd $(date) mod=$MODDIR" >"$log"
rm -f "$MODDIR/disable"
f=libmmcamera_imx230.so
src=""
for cand in "$MODDIR/$f" "$MODDIR/system/vendor/lib/$f"; do
  if [ -f "$cand" ]; then
    src=$cand
    break
  fi
done
echo "pick $f src=$src" >>"$log"
[ -n "$src" ] || exit 0
mount -o rw,remount /vendor 2>/dev/null || true
for dst in "/vendor/lib/$f" "/system/vendor/lib/$f"; do
  umount "$dst" 2>/dev/null || true
  cp "$src" "$dst" || { echo "cp fail $dst" >>"$log"; continue; }
  chown root:root "$dst"
  chmod 644 "$dst"
  chcon u:object_r:vendor_file:s0 "$dst" 2>/dev/null || true
  restorecon "$dst" 2>/dev/null || true
  echo "installed $dst" >>"$log"
done
"""

SERVICE = b"""#!/system/bin/sh
# Ident is delayed ~8s; qcamerasvr probes at ~6s and misses g_sctrl.
# Restart the daemon once Hill is bound.
sleep 12
kill -9 $(pidof mm-qcamera-daemon) 2>/dev/null || true
stop qcamerasvr
start qcamerasvr
"""

PROP = b"""id=talkman-smia
name=talkman SMIA camera HAL
version=12
versionCode=12
author=talkman
description=libmmcamera_imx230.so + restart qcamerasvr after ident
"""


def main() -> None:
    src = OUT / "libmmcamera_imx377.smia9.so"
    d = bytearray(src.read_bytes())
    name = bytes(d[SENSOR_NAME_OFF : SENSOR_NAME_OFF + 32]).split(b"\x00", 1)[0]
    if name != b"imx377":
        raise SystemExit(f"sensor_name at 0x{SENSOR_NAME_OFF:x} is {name!r}")
    d[SENSOR_NAME_OFF : SENSOR_NAME_OFF + 32] = b"imx230" + b"\x00" * 26
    n = d.count(SONAME)
    if n != 1:
        raise SystemExit(f"expected 1 {SONAME!r}, found {n}")
    d = d.replace(SONAME, SONAME_NEW)
    if b"imx377" not in d[0x271c:0x2900]:
        raise SystemExit("chromatix imx377_* strings vanished")
    if d[SENSOR_NAME_OFF : SENSOR_NAME_OFF + 6] != b"imx230":
        raise SystemExit("sensor_name patch lost")

    LIBDIR.mkdir(parents=True, exist_ok=True)
    out_so = OUT / "libmmcamera_imx230.so"
    out_so.write_bytes(d)
    (MOD / "libmmcamera_imx230.so").write_bytes(d)
    (LIBDIR / "libmmcamera_imx230.so").write_bytes(d)
    (MOD / "post-fs-data.sh").write_bytes(PFSD.replace(b"\r\n", b"\n"))
    (MOD / "service.sh").write_bytes(SERVICE.replace(b"\r\n", b"\n"))
    (MOD / "module.prop").write_bytes(PROP)

    zip_path = OUT / "talkman-smia-v12.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("module.prop", PROP)
        z.writestr("post-fs-data.sh", PFSD.replace(b"\r\n", b"\n"))
        z.writestr("service.sh", SERVICE.replace(b"\r\n", b"\n"))
        z.writestr("libmmcamera_imx230.so", d)
        z.writestr("system/vendor/lib/libmmcamera_imx230.so", d)
    print("wrote", out_so, len(d))
    print("wrote", zip_path, zip_path.stat().st_size)


if __name__ == "__main__":
    main()
