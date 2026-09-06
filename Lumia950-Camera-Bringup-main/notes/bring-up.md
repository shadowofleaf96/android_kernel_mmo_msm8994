# Talkman camera bring-up

Short working note (read first): [`work.md`](work.md).

**Status:** see [`handoff.md`](handoff.md) (2026-08). Ident and HAL1 TG
preview work; live CSI is ECC. This file is the flash chronology.

**PR:** https://github.com/Android4Lumia950/android_kernel_mmo_msm8994/pull/4
(`EpicLPer:talkman-smia65pp` → `lineage-18.1-skip-fw-cache`)

Snaccy’s last guidance: treat power/ident as the **default SMIA++**
sequence (`smiapp_power_on`). He does not have a next hardware step
beyond that. A kernel PR is reasonable **after** a cleanup pass; this
file is the record so that pass does not drop facts.

## What is proven

- WP sensors are **SMIA++**. qcamera talks to Nokia-style `qcom,smia65pp`,
  not bullhead IMX377/OV5693. Rear HAL name is **imx230**.
- **3.10 `CONFIG_VIDEO_SMIAPP` cannot bind these nodes.** It is an
  `i2c_driver` that wants `platform_data`. CCI is not an `i2c_adapter`.
  Do not put `nokia,smia` on the CCI children. Ident is
  `smiapp-reg-defs.h` over MSM CCI inside `smia65pp.c`.
- One **`s_ctrl` per device** (kzalloc). A static singleton crashed
  snaccy with two cameras.
- `reg` is the **8-bit I2C address** (Hill/front `0x20` → CCI sid
  `0x10`; iris `0x6C` → `0x36`). Two `0x20` nodes cannot both be named
  `cam` (`of_device_make_bus_id` is `$reg.$name`) → `cam0@0` / `cam1@1`
  / `cam2@2`.
- Live CCI dump (userspace, kernel #5) already read real modules:

  | Camera | CCI | 7-bit | Module | Size | Lanes |
  |---|---|---|---|---|---|
  | Hill rear | master 1 | `0x10` | `0xEACA` Sharp | 5344×4016 | 4, RAW10 |
  | Front (Ducati) | master 0 | `0x10` | `0x2140` Sharp | 2600×1952 | 2, RAW10 |
  | Iris | master 0 | `0x36` | not dumped | — | — |

  Nokia X2 leftover `0x563A` is Toshiba RAISU, not these modules.
  snaccy’s old table had Hill/Ducati IDs **swapped**.
- ACPI wiring (talkman `asl_files/camera.asl`, **not** `camera_mtp.asl`)
  matches Hill: CCI1, CSI0, GPIO 13/92/91, L25/L29/LVS1/L23.

## Current blocker

Live Hill CSI: uncorrectable CSID ECC after the test generator is off.
HAL1 paints TG only. Full list: [`handoff.md`](handoff.md).

Hardware path with TG is live: ISPIF PIX SOF, CAMIF SOF+EOF, AXI
viewfinder buf_done, kernel `ISP_EVENT_SOF`. **HAL3** times out. Keep
`persist.camera.HAL3.enabled=0`. Front/iris stay disabled.

XML `CFG_SINIT_PROBE` / capability are already past the old -22 slot
bind. That paragraph is historical (kernels #16–#18). See [`work.md`](work.md)
and [`camif.md`](camif.md).

WP `qccamrearsensor_primarySMIApp8992.sys` is a SMIApp wrapper: PowerOn,
ident (`cam_drv_0AEACA_*` = Hill module `0xEACA`), 1 MHz CCI, 4-lane CSI,
CDCC/NVM, then `SMIApp_StartStream`. That last part is qcamera HAL on
Linux, not another kernel ident flash.

smia-msm **#15** (uname **#33**): delayed `msm_sensor_platform_probe`
after ident. CSI lanes from snaccy’s DT (`0x4320` / `0x1F`). No LVS1 in
`qcom,cam-vreg-name`. Do **not** call that probe from nested CCI populate.

## Do not bootloop

These are settled. Full list: `.cursor/rules/talkman-camera.mdc`.

| Don’t | Why |
|---|---|
| `sensor_power_up` / `power_down` at kernel init | TWRP ID path. Shared LVS1 + GPIO + daemon. #1–#3. |
| `msm_sensor_platform_probe` from CCI populate | #4 still died (`get_dt_data` + V4L2 + `msm_sd_register`). |
| `-EPROBE_DEFER` or `msm_sd_register` in the nested CCI child probe | `of_platform_populate` runs **before** `g_cci_subdev`. |
| Dereference `pdev->id_entry` | NULL on DT devices; `CDBG` still evaluates args. |
| `regulator_disable` LVS1 / put `CAM_VIO` in `msm_sensor` power_setting | Cutting shared 1.8V reboots the board. **Enable and hold is OK** (#11). |
| Release xshutdown before MCLK | #9 NACKed that way. |
| `compat_ioctl32 = v4l2_compat_ioctl32` on VFE | #111. MSM ioctls hit default → `fops->compat_ioctl32` recurse. Wrap nr 89 only. |
| Omni recovery `/sys/fs/pstore` | Bullhead maps ramoops at `0x1fe00000`; talkman is `0x070A0000`. |

## Kernel series (smia-msm)

`uname` `#n` is the local build counter, not the smia-msm number.

| smia-msm | uname | Image | Result |
|---|---|---|---|
| (pre) | **#18** | `out/boot-now.img` | Last pre-SMIA Android. Emergency restore. |
| #1–#4 | — | — | Bootloop. No usable pstore. |
| #5 | #23 | `out/boot-smia5.img` | Skeletal bind. Live dump from here. |
| #6 | #24 | — | Parse-only identity. |
| #7 | #25 | — | config32 + CCI sid, Hill only. |
| #8 | #26 | `/sdcard/boot-smia8.img` | 3 nodes, no power. |
| #9 | #27 | `/sdcard/boot-smia9.img` | Reset **before** MCLK → NACK. |
| #10 | #28 | `out/boot-smia10.img` | smiapp xshutdown order, no VIO. Still NACK. |
| **#11** | **#29** | `out/boot-smia11.img` | VIO hold + ACPI standby + `0x0103`. Still NACK. |
| **#12** | **#30** | `out/boot-smia12.img` | 3-cam ident, no VIDEO_SMIAPP. Still NACK. Magisk ramdisk base. |
| **#13** | **#31** | `out/boot-smia13.img` | Hill-only + L23. Clock on, **GPIO 13 unclaimed**. NACK. |
| **#14** | **#32** | `out/boot-smia14.img` | `cam_default` pinctrl. Hill ident 0xEACA / IMX230 0x0230. |
| **#15** | **#33** | `out/boot-smia15.img` | Delayed qcamera register. `v4l-subdev13` = imx230. |
| **#16** | **#34** | `out/boot-smia16.img` | `g_sctrl[0]` bind. 1 camera. Preview: Invalid ISP `INPUT_CFG`. |
| — | **#35** | `out/boot-smia17.img` | `hbi_cnt` (INPUT_CFG 148). Preview: Invalid ISP `CFG_STREAM` 36. |
| — | **#36** | `out/boot-smia18.img` | CFG_STREAM 36. Preview: CPP `num_buffs==0`, SOF freeze. |
| — | **#37** | `out/boot-smia19.img` | CPP `num_buffs==0`. Preview: SOF freeze. |
| — | **#38** | `out/boot-smia20.img` | CSIPHY/CSID clamp. Preview: CSID IRQ `0x20000dd`. |
| **#17** | **#39** | `out/boot-smia21.img` | START_STREAM wrapper; 0 cameras (`copy_from_user`). |
| **#18** | **#40** | `out/boot-smia22.img` | Peek `cfgtype`; 1 camera. Preview: CSID `0x20000dd`. |
| **#19** | **#41** | `out/boot-smia23.img` | Crop+WOA PLL; CCI reads 0; CSID quiet. |
| **#20** | **#42** | `out/boot-smia24.img` | Crop + `0x0100`; native PLL; CSID `0x20000dd`. |
| **#21** | **#43** | `out/boot-smia25.img` | Crop + WOA PLL + `0x0100` on table #1; CCI 0. |
| **#22** | **#44** | `out/boot-smia26.img` | WOA PLL; `0x0100` after CSIPHY; CCI 0; CSID `0x800`. |
| **#23** | **#45** | `out/boot-smia27.img` | Native PLL; `0x0100` after PHY; CSID `0x20000dd`. |
| **#24** | **#46** | `out/boot-smia28.img` | CSID stats: pkts+ECC, `sig=0x2`. |
| **#25** | **#47** | `out/boot-smia29.img` | Force `0x0111=0`; write ignored. |
| **#26** | **#48** | `out/boot-smia30.img` | `0x3210`: pkts=0, IRQ `0xd000dd`. |
| **#27** | **#49** | `out/boot-smia31.img` | `0x0234`: same pkts+ECC as 0x4320. |
| **#28** | **#50** | `out/boot-smia32.img` | settle `0x28`; still pkts+ECC. |
| **#29** | **#51** | `out/boot-smia33.img` | DPHY_CTRL=UI, `0x0820=0`. |
| **#30** | **#52** | `out/boot-smia34.img` | SMIA `0x0820` 1×op_sys; still ECC. |
| **#31** | **#53** | `out/boot-smia35.img` | SMIA `0x0820` 2×op_sys; still ECC. |
| **#32** | **#54** | `out/boot-smia36.img` | Colour bars `0x0600=2`; still ECC. |
| **#33** | **#55** | `out/boot-smia37.img` | DPHY_CTRL automatic; still ECC. |
| **#34** | **#56** | `out/boot-smia38.img` | SMIA max4 bitrate dump. |
| **#35** | **#57** | `out/boot-smia39.img` | NVM page 0 real; CSID still pkts+ECC. |
| **#36** | **#58** | `out/boot-smia40.img` | CSIPHY `lnn_misc1` bit 0 invert; same ECC. |
| **#37** | **#59** | `out/boot-smia41.img` | CSID `0x4302` ln0=phy2; same ECC. |
| **#38** | **#60** | `out/boot-smia42.img` | CSID `0x4203` ln0=phy3; same ECC. |
| **#39** | **#61** | `out/boot-smia43.img` | CSIPHY lane dump; cfg4=0x5 cfg5=0x52; 0x4320. |
| **#40** | **#62** | `out/boot-smia44.img` | **Restore.** Late PHY irq 0x4 all lanes; still ECC. |
| **#41** | **#63** | `out/boot-smia45.img` | half CSI `op_sys=2`; same ECC. |
| **#42** | **#64** | `out/boot-smia46.img` | CFG4 0x5→0x4 stuck; still pkts+ECC. |
| **#43** | **#65** | `out/boot-smia47.img` | CFG4=0; CSID silent. Do not flash. |
| **#44** | **#66** | `out/boot-smia48.img` | WOA 1/66 at table 7; CCI dies. Do not flash. |
| **#45** | **#67** | `out/boot-smia49.img` | CDCC 1/124 stuck; CCI ok; CSID silent (`0x800`). |
| **#46** | **#68** | `out/boot-smia50.img` | CDCC idle on ident 4/177; CSID silent. |
| **#47** | **#69** | `out/boot-smia51.img` | idle then 1/124; CSID silent. |
| **#48** | **#70** | `out/boot-smia52.img` | mode-0 vendor on 4/177; pkts+ECC again. |
| **#49** | **#71** | `out/boot-smia53.img` | CDCC override 0x1bxx; readback 0; pkts+ECC. |
| **#50** | **#72** | `out/boot-smia54.img` | CSIPHY data-only invert; same pkts+ECC. |
| **#51** | **#73** | `out/boot-smia55.img` | CSIPHY clock-only invert; same pkts+ECC. |
| **#52** | **#74** | `out/boot-smia56.img` | WP CSID CORE_CTRL_1 `0x1000F`; MISR live; same ECC. |
| **#53** | **#75** | `out/boot-smia57.img` | CSID TG `0xa06437`; CORE_CTRL skipped; CSID silent. |
| **#54** | **#76** | `out/boot-smia58.img` | TG+CORE_CTRL; MMIO stuck; TG pkts; ECC low-half; black. |
| **#55** | **#77** | `out/boot-smia59.img` | skip 0x0100 at table 7; HAL table 8 set it; TG-only no 0xdd. |
| **#56** | **#78** | `out/boot-smia60.img` | force 0x0100=0; isolate holds; TG SOF only; no 0xdd; black. |
| **#57** | **#79** | `out/boot-smia61.img` | TG_VC num DT=3 (`0x8080000c`); still long=0; ECC 0x30001. |
| **#58** | **#80** | `out/boot-smia62.img` | CAF num DT=0 + TG payload 0x55/0xAA; SOF IRQs; long=0; black. |
| **#59** | **#81** | `out/boot-smia63.img` | TG CORE_CTRL without `0x4320`; IRQ `0x2000000`; no SOF. |
| **#60** | **#82** | `out/boot-smia64.img` | restore 0x4320; map 0x70=0; still black. |
| **#61** | **#83** | `out/boot-smia65.img` | TG DT0 pixel width; uncorrectable; **do not flash**. |
| **#62** | **#84** | `out/boot-smia66.img` | CAF bpl + PHY pwr=0; HS-lock gone; TG SOF; long=0. |
| **#63** | **#85** | `out/boot-smia67.img` | **ISPIF PIX SOF ~37 fps.** CAMIF error `0xff8`. Black. |
| **#64** | **#86** | `out/boot-smia68.img` | CAMIF SOF lockstep, **never EOF**, clk=480 MHz, st=`0xff8` = 4088 px. |
| **#65** | **#87** | `out/boot-smia69.img` | ppl 4088; **overflow gone**; still never EOF. |
| **#66** | **#88** | `out/boot-smia70.img` | CAMIF 1-line; st=`0xbd40000` = **3028 lines**. Do not flash. |
| **#67** | **#89** | `out/boot-smia71.img` | full window 0..4087×0..3027; no error; still never EOF. |
| **#68** | **#90** | `out/boot-smia72.img` | 0x31C **st=0x0 at every SOF**; s1=0; still no EOF. |
| **#69** | **#91** | `out/boot-smia73.img` | mid-frame **st=0x0** cmd=1 cfg=0x40 extra=`0xaadc0000`. |
| **#70** | **#92** | `out/boot-smia74.img` | pixclk 200 MHz; error **0x15f8=5624 px**; pixels live. Revert. |
| **#71** | **#93** | `out/boot-smia75.img` | pixclk 320 MHz; error **0x1a48=6728 px**. Revert. |
| **#72** | **#94** | `out/boot-smia76.img` | pixclk 600 MHz; no overflow; SOF+EPOCH; never EOF. |
| **#73** | **#95** | `out/boot-smia77.img` | CAMIF EFS 0x2FC=0x00200040; still no EOF. |
| **#74** | **#96** | `out/boot-smia78.img` | epoch0=3027 **fires every frame**; next SOF 0.5 ms; no EOF. |
| **#75** | **#97** | `out/boot-smia79.img` | TG V-blank 0xFF; SOF gap 1.0 ms; still no EOF. |

Magisk su: `/debug_ramdisk/su`. Boot
`mmcblk0p37` / `by-name/boot`. After each flash: `dmesg`, not
`logcat -b kernel` (stale pstore lines).

## What is left (ordered)

Current gap: **live Hill CSI ECC**. CAMIF EOF was found (masked). See
[`handoff.md`](handoff.md). Historical notes below are kept so old
kernels are not re-tried as “EOF fixes”.

1. **CAMIF EOF** — CAMIF counts all 3028 lines (epoch 3027). ISPIF has
   PIX EOF (`st0=0x7`); CAMIF never sets irq bit1. V-blank 0xFF still no
   CAMIF EOF. Next: last_line=3026 or CAMIF syncMode EFS. See [`camif.md`](camif.md).
   Keep TG isolate. Do not 200/320 MHz or 1-line CAMIF.
2. **CSI headers** — PHY still 100% ECC when isolate is off. After preview
   on TG, re-test PHY. `long=0` is not “no frames”.
3. **Front / iris** — re-enable after Hill previews.

Magisk su: `/debug_ramdisk/su`. Boot
`mmcblk0p37` / `by-name/boot`. After each flash: `dmesg`, not
`logcat -b kernel` (stale pstore lines).

## What is left (ordered)

1. **Live CSI / Hill scene** — HAL1 paints TG. `0x0100=1` from HAL table 8.
   Turning TG off → no PIX SOF. Clock is phy1 (WP `0x4320`): irq `0x20000dd`.
   Other clock phys: `0xe000dd` / `0xd000dd`. Data `0x3420`: `0x80000dd`.
   Analog `0xb04x` stuck. Never-TG + early `0x0100` froze at table 5 (#112).
   `pn_invert` is already 0. Do **not** repeat CDCC idle (#68). Keep TG
   until PHY SOF exists. Next: data permutes `0x2430` / `0x2340` / `0x0432`.
2. **Front / iris** — re-enable after Hill previews.

## PR vs this repo

This folder is a **scratch + overlay** tree. The kernel that actually
builds is an `android_kernel_mmo_msm8994` checkout (branch
`lineage-18.1-skip-fw-cache`). Set `KERNEL_TREE` at that checkout.

**Keep / intended PR payload**

- `dts/msm8992-talkman-camera.dtsi`
- `kernel/smia65pp.c`
- `scripts/apply-to-mmo-talkman.sh`, `apply-smia-boot-safe.py`, `apply-smia-qcam-slot.py`
- `scripts/remote-rebuild-cam.sh`, `remote-cam-lib.sh`, `bootimg.py`
- `asl_files/` (talkman ACPI)
- `notes/` and this file
- Kconfig/`SMIA65PP` + `chi.dtsi` include swap (done by apply script)

**Do not put in a first PR**

- `out/` boot images, dmesg, Magisk zips (gitignored; keep locally)
- `scripts/patch-smia*.py`, `apply-csi-*.py`, `apply-isp-*.py`,
  `libmmcamera_imx377` overlays — bullhead IMX377 dead-end. Keep on
  disk; they are not the SMIA++ path.
- `CONFIG_VIDEO_SMIAPP=y` — **removed** in smia-msm #12 / this PR.
- Ident `pr_err` spam and the 8 s delayed work — fine for bring-up,
  too loud to merge as a finished camera driver.

**PR must not** call `msm_sensor_platform_probe` at init, must not
disable LVS1, must keep one `s_ctrl` per node.

## Build / flash

```text
wsl:  scripts/apply-to-mmo-talkman.sh
wsl:  scripts/remote-rebuild-cam.sh          # optional remote host via remote-cam.env
pack: bootimg.py replace-kernel out/boot-smia12.img out/Image.gz-dtb-cam out/boot-cam.img
      (use out/boot-now.img only when restoring kernel #18)
flash: adb push → /debug_ramdisk/su dd …/by-name/boot → reboot
```

`scripts/remote-cam.env` is local (not committed). Cursor and adb stay
on this PC.

## Related notes

- `notes/snaccy-verified.md` — early ACPI vs snaccy DT audit
- `notes/smia-live-dump.md` — register dump from kernel #5
- `notes/camif.md` — VFE44 CAMIF SOF/EOF/status decode
- `.cursor/rules/talkman-camera.mdc` — hard constraints for later flashes
