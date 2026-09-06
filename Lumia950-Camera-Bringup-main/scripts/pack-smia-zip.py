#!/usr/bin/env python3
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "out"
SCRIPT = (OUT / "magisk-talkman-smia" / "post-fs-data.sh").read_bytes().replace(b"\r\n", b"\n")
PROP = b"""id=talkman-smia
name=talkman SMIA camera probe
version=10
versionCode=10
author=talkman
description=SMIA 4080 crop + ROM 53.1 MHz vt (no PLL override)
"""
imx = (OUT / "libmmcamera_imx377.smia7.so").read_bytes()
ov = (OUT / "libmmcamera_ov5693.smia7.so").read_bytes()
zip_path = OUT / "talkman-smia-v10.zip"
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("module.prop", PROP)
    z.writestr("post-fs-data.sh", SCRIPT)
    z.writestr("libmmcamera_imx377.so", imx)
    z.writestr("libmmcamera_ov5693.so", ov)
    z.writestr("system/vendor/lib/libmmcamera_imx377.so", imx)
    z.writestr("system/vendor/lib/libmmcamera_ov5693.so", ov)
print("wrote", zip_path, zip_path.stat().st_size)
print(zipfile.ZipFile(zip_path).namelist())
