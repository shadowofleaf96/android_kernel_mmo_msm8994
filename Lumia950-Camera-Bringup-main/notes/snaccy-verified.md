# Camera notes (snaccy + ACPI)

Bring-up status (current kernel, CCI NACK, restore images):
[`bring-up.md`](bring-up.md). This file is the durable snaccy + ACPI
record. Live CCI dumps **swapped** his Hill/Ducati model IDs (`0xEACA`
is Hill, `0x2140` is front).

## Quoted snaccy (do not drop)

- “the sensor should be imx230 this isn't bullhead”
- “make it pull the info via the smia++ driver”
- “search smia in the current tree and use the Nokia smia driver for reference”
- “make it use smia++ strictly” / use the `smiapp` branch
- “it should basically make a smia driver that will act as a MSM sensor”
- “the cameras need to both use qcamera stuff and also smia++” → Nokia X2 `smia65pp`
- Two cameras crashed for him constantly → **one `s_ctrl` per device**; his DT is **Hill only**
- Repo: https://github.com/Android4Lumia950/android_kernel_msft_talkman/tree/smiapp
- Nokia X2 pattern: https://github.com/cm-nokia-x2/android_kernel_nokia_msm8610/commit/af0b55472a6af207689e3681274f54ed9a6dbeaa
- `ice5lp_2k` is the USB-C **UC120** FPGA (WOA Ice5Lp2k), **not** camera OIS. Camera OIS is `qcom,ois` / SMIApp. Do not claim GPIO 53/54.

snaccy’s Hill node (reference — **do not copy the VIO/VAF name swap**):
https://raw.githubusercontent.com/Android4Lumia950/android_kernel_msft_talkman/smiapp/arch/arm64/boot/dts/lumia/camera.dtsi

| Rail | ACPI CAMS D0 | Our DT name | snaccy `camera.dtsi` name |
|---|---|---|---|
| L25 1.15 V | analog/core | `cam_vdig` | `cam_vdig` |
| L29 2.85 V | analog | `cam_vana` | `cam_vana` |
| LVS1 1.8 V | **VIO, shared** | **`cam_vio`** (never disable) | he called this `cam_vaf` |
| L23 2.85 V | extra analog | **`cam_vaf`** | he called this `cam_vio` |

## What snaccy said, and what checks out

| Claim | Verdict |
|---|---|
| WP cameras are SMIA++ | **Yes.** Nokia/QCOM wrapper is `smia65pp.c` (SMIA model @ 0x0000, manufacturer @ 0x0003). |
| 3.10 mainline `smiapp` is not QCAM | **Yes.** `drivers/media/i2c/smiapp` is V4L2. QCAM needs `camera_v2` (`qcom,smia65pp`). Binding both is why “Android will crash” / “cannot handle 2 SMIA drivers”. |
| Nokia X2 commit is the QCAM pattern | **Yes.** https://github.com/cm-nokia-x2/android_kernel_nokia_msm8610/commit/af0b55472a6af207689e3681274f54ed9a6dbeaa (`smiapp.c` / `smia65pp.c` + eeprom/actuator). |
| `smiapp` branch IDs a sensor in TWRP | **Plausible.** `lumia/camera.dtsi` enables **Hill only**. Front + iris are commented. |
| Iris + front on CCI0, rear on CCI1 | **Matches ACPI `INFO`.** `camera.asl` returns `0x060000`: bit 16 = 0 (front CCI0), bit 17 = 1 (back CCI1). |
| DT is ACPI-based and likely wrong in places | **Yes.** See mismatches below. |
| No public schematic for CCI1 Hill | **Unverified.** ACPI + snaccy DT are the source. |
| Nothing actually previewed | **Yes.** ID only. |

`camera.asl` is talkman (GPIOs 102/106). `camera_mtp.asl` is Qualcomm MTP (94/93) — do not use it for talkman.

## ACPI devices

| ACPI | HID | CSI | MCLK | RST / STANDBY (CAMP) | Rails (D0) | Role |
|---|---|---|---|---|---|---|
| CAMS | QCOM2434 | CSI0 / PHY0 irq 83 | mclk0 9.6 MHz, GPIO 13 | 92 / 91 (CAMSENSOR_1) | LDO23 2.85, LDO29 2.85, LDO25 1.15, LVS1 1.8 | **Hill rear** |
| CAMF | QCOM2439 | CSI2 / PHY2 irq 85 | mclk2 9.6 MHz, GPIO 15 | 104 / 105 (WEBCAM1) | LDO17 2.80, LVS1 1.8 | **Front (Ducati)** |
| CAMT | QCOM2436 | CSI3 irq 86 | mclk1 9.6 MHz, GPIO 14 | 102 (CAMSENSOR_2) | LDO17 2.80, LVS1 1.8, LDO3 1.2, SMPS3, boost | **Iris** |

CAMP also lists CCI MMIO `0xFDA0C000` irq 82 (standard 8992 CCI).

## snaccy `lumia/camera.dtsi` vs ACPI

Hill (enabled): CCI **master 1**, CSI0, GPIO 13/92/91, L25/L29/L23/LVS1 — **matches CAMS**. Keep this node first.

Commented “Ducati”: GPIOs 102/106 (that is CAMSENSOR_2 / iris, not webcam). MCLK gpio 14 vs clocks `mclk2`. Copy-paste.

Commented iris: CCI **master 1** (snaccy said CCI0), GPIOs 104/105 (webcam, not CAMT). CSID 3 is right for CAMT.

`msm8992-chi.dtsi` on the smiapp branch **also** `#include`s `msm8992-camera-sensor-mtp.dtsi`. That is a second sensor stack. This overlay replaces that include with `msm8992-talkman-camera.dtsi` (three `qcom,smia65pp` nodes).

`talkman/msm8992-talkman-camera.dtsi` is a Nokia X2 kang (`pm8110`, `ov7695`) and is **commented out**. Ignore it.

## `smia65pp` ID table (snaccy’s comments were swapped)

Live dump (kernel #5, [`smia-live-dump.md`](smia-live-dump.md)):

- Hill rear: model **`0xEACA`**, Sharp, 5344×4016. Inner SMIA sensor **`0x0b-0x0230`** (Sony IMX230) — kernel #14 dmesg. WP rear KMD has `cam_drv_0AEACA_*` (same module ID) and `Setting i2c_speed to = 1000 KHz`.
- Front Ducati: model **`0x2140`**, Sharp, 2600×1952
- DT leftover `0x563A` is Nokia X2 Toshiba RAISU — ignore it

snaccy’s `smiapp` branch comments had Hill/Ducati the other way around.
Ident here logs whatever CCI returns; it does not require that table.

## Magisk vs kernel

Sensor probe is kernel + DTB. Magisk cannot replace `cci` / `smia65pp`. After ident, Magisk supplies `libmmcamera_imx230.so` (`scripts/pack-imx230.py`).

Do not enable `CONFIG_VIDEO_SMIAPP` together with `qcom,smia65pp`.
