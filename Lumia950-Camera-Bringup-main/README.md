# Lumia 950 (RM-1104 / talkman) — camera bring-up

Overlay and notes for the three SMIA++ sensors (Hill rear / Ducati front
/ iris) on the community Android port.

**Start here:** [`notes/handoff.md`](notes/handoff.md).

This is **not** a working scene preview. Ident and qcamera HAL1 work.
The pixels you get are the **CSID test generator**. Live Hill CSI is
uncorrectable ECC. That is documented so the next person does not
re-walk the same CAMSS lottery.

## Status

| | |
|---|---|
| Hill ident (`0xEACA` / inner `0x0230`) | works |
| qcamera name `imx230`, HAL1 preview | works (pink TG pattern) |
| Live sensor CSI | **blocked** — CSID header ECC after TG-off |
| Front / iris preview | not started (nodes stay disabled) |
| HAL3 | times out; keep `persist.camera.HAL3.enabled=0` |

Kernel bind (safe probe, no power at init):
[Android4Lumia950/android_kernel_mmo_msm8994#4](https://github.com/Android4Lumia950/android_kernel_mmo_msm8994/pull/4).
That PR still describes CCI NACK; ident was fixed later in this overlay.

Snaccy’s architecture branch:
[android_kernel_msft_talkman `smiapp`](https://github.com/Android4Lumia950/android_kernel_msft_talkman/tree/smiapp).

## Path (do not rediscover)

WP modules are SMIA++. qcamera talks to Nokia X2-style `qcom,smia65pp`.
Rear HAL identity is **imx230**, not bullhead IMX377/OV5693.

Do not enable `CONFIG_VIDEO_SMIAPP` on these CCI children. 3.10 smiapp
is an I2C driver; CCI is not an `i2c_adapter`. Ident is
`smiapp-reg-defs.h` over CCI inside `kernel/smia65pp.c`.

Never `sensor_power_up` / `power_down` or `msm_sensor_platform_probe` at
CCI populate. Never disable PM8994 LVS1 (shared 1.8 V).

## Layout

| Path | What |
|---|---|
| `notes/handoff.md` | Handoff: works, roadblock, exhausted list, dumps |
| `notes/work.md` | Short lab log (last flashes) |
| `notes/bring-up.md` | Kernel-number chronology |
| `notes/camif.md` | VFE44 CAMIF SOF/EOF |
| `notes/ghidra-csiphy.md` | WP CSIPHY/CSID vs Linux |
| `notes/snaccy-verified.md` | ACPI vs snaccy DT |
| `dts/msm8992-talkman-camera.dtsi` | Three `qcom,smia65pp` CCI children |
| `kernel/smia65pp.c` | MSM wrapper + delayed ident |
| `asl_files/` | ACPI. Use `camera.asl`, not `camera_mtp.asl` |
| `scripts/apply-to-mmo-talkman.sh` | Copy DT/C into the mmo kernel tree |

Boot images in `out/` are gitignored (local lab only).

## Building

Needs a checkout of
[`android_kernel_mmo_msm8994`](https://github.com/Android4Lumia950/android_kernel_mmo_msm8994)
(branch used here: `lineage-18.1-skip-fw-cache`) and an aarch64 GCC.

```bash
export KERNEL_TREE=/path/to/mmo_msm8994_talkman
# copy overlay DT + smia65pp.c into that tree
bash scripts/apply-to-mmo-talkman.sh
# then build Image.gz + dtbs in the kernel tree as usual
```

Remote-build helpers read `scripts/remote-cam.env` (not committed; copy
`scripts/remote-cam.env.example`).

## HAL / Magisk

Sensor probe is **kernel + DTB**. Magisk cannot replace CCI/`smia65pp`.
After dmesg shows `smiapp: module 0x0a-0xeaca`, bind
`libmmcamera_imx230.so` as `0644` `vendor_file` via Magisk (`su -M`).
Never bind it from `/sdcard`.

Open Camera: do not swipe-up after launch (that opens Settings).

## License

Kernel overlay (`kernel/smia65pp.c`, DT) follows the kernel it patches
(GPL-2.0). Notes are CC0 unless a file says otherwise.
