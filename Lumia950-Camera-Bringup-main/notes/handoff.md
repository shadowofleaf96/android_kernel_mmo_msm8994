# Talkman camera handoff (RM-1104 / Hill)

This is the document to read if you are picking up Lumia 950 rear-camera
bring-up. Short lab log: [`work.md`](work.md). Flash chronology:
[`bring-up.md`](bring-up.md). Snaccy / ACPI: [`snaccy-verified.md`](snaccy-verified.md).
CAMIF decode: [`camif.md`](camif.md). WP CSIPHY/CSID: [`ghidra-csiphy.md`](ghidra-csiphy.md).

**Status (2026-08):** ident and qcamera HAL1 preview work. The pixels
on screen are the **CSID test generator**, not the sensor. Live Hill
CSI is **uncorrectable header ECC**. That gap was exhausted against
Windows Phone dumps, KMDs, and DCC. It is not a missing CSID LUT,
settle, or CGC mux.

## What this is

Windows Phone sensors on talkman are **SMIA++**. Android qcamera
(`mm-qcamera-daemon`) talks to a Nokia X2-style MSM wrapper
(`qcom,smia65pp`). Rear HAL name is **imx230**, not bullhead IMX377.

Snaccy IDed Hill only (no public Linux/WOA port has a live scene).
Quoted guidance (keep): SMIA++ strictly; Nokia `smia65pp` acting as an
MSM sensor; one `s_ctrl` per device; Hill first; `camera.asl` not MTP;
`ice5lp_2k` is the USB-C **UC120 FPGA**, not a camera part.

Kernel bind PR (early, ident still NACKed):
[Android4Lumia950/android_kernel_mmo_msm8994#4](https://github.com/Android4Lumia950/android_kernel_mmo_msm8994/pull/4).
Ident is solved in this overlay; do not restart from that PR’s NACK
state.

## What works

| Piece | Result |
|---|---|
| Delayed `qcom,smia65pp` bind | Probe at CCI populate is bind-only. No `sensor_power_up` / `msm_sensor_platform_probe` there (bootloop #1–#4). |
| Hill ident | Module **`0xEACA`** (Sharp), inner Sony **`0x0230`**, 5344×4016, CCI1, 8-bit `0x20`. |
| Front ident (when enabled) | **`0x2140`**, 2600×1952, CCI0, 2-lane. Iris `0x6C` from snaccy, not live-dumped. |
| qcamera slot | Delayed `msm_sd_register` → `v4l-subdev` name **`imx230`**. Needs Magisk `libmmcamera_imx230.so`. |
| HAL1 preview | Paints. `PROFILE_FIRST_PREVIEW_FRAME`. Keep `persist.camera.HAL3.enabled=0`. |
| HAL3 | Capture requests time out → black Surface. Do not use for this work. |
| ISPIF | PIX SOF ~37 fps with CSID TG. |
| VFE44 CAMIF | SOF + EOF (EOF was always there; CAF mask `0xF5` hid bit1). |
| AXI | Viewfinder buf_done + `BUF_DIVERT` DQEVENT `0x8000101`. |
| CSID TG | Incrementing pattern (pink scanlines). This is **inside the SoC**, not the sensor. |
| WP dumps | Rear VF MMIO, CCI timing, QcomCamera ETL, `0AEACA05.dcc`, Ghidra of rear/platform/core/ISP KMDs. |

Daily image on the lab Android unit was **`out/boot-smia113.img`**
(uname **#131**): TG stays on, idle analog `0xb04x`, HAL1 pink
viewfinder, UI usable. That file is local/`gitignored`, not in this
repo.

## The roadblock

After HAL streams, turning the CSID test generator **off** leaves
live CSI. 4-lane irq is **`0x20000dd`**. CSID 3.0 bit `0x02000000` is
**uncorrectable ECC**. `map=0`. No ISPIF PIX SOF without TG.

Clock is **phy1** (`lane_assign 0x4320`), matching WP. Wrong clock
phys change the irq (`0xe000dd` / `0xd000dd`) and are not the gap.

Colour bars (`0x0600=2`) still ECC. The sensor is outputting
*something*; the 20nm D-PHY/CSID path cannot parse the headers.

**TG is a crutch.** Never-TG + early `0x0100=1` makes Open Camera fail
to open (#112). TG-off daily kernels storm CSID irqs and freeze the UI.

## What is *not* the gap (do not lottery)

Tried on device, still ECC after TG-off unless noted:

| Class | Examples |
|---|---|
| CSID lane map | `0x4320` (WP) plus permutes `0x4321`/`0x4310`/`0x4210`/`0x3420`/`0x4230`/`0x2430`/`0x2340`. 2-lane `0x20` → PHY overflow, not a scene. `0x40` silent. |
| CSID CORE_CTRL_1 | WP `0x1000F` (#74). MISR became live; still ECC. |
| CSID LUT | WP VF `DT 0x30` / CID `0x51` DPCM 10-8-10 (#146). Headers fail **before** the LUT. |
| CSIPHY analog | Live WP CFG2=`0x3f` CFG3=`0x16` CFG4=`0xff` CFG5=`0x22` test_imp=`0x17` +0x2c=`0x70` (#139–#141). |
| Settle / invert | HAL `0x1b`, force `0x28`, WP `0x16`. `pn_invert` already 0. Data-only / clock-only invert. CFG4=0 **silences** CSID. |
| Sensor D-PHY | `0x0808` UI/REGISTER/auto, `0x0820` several rates including WP VF `0x0bd9`, extclk `0x0999`, colour bars. |
| PLL / window | Ident 4/177 (only PLL that makes CSID see packets). DCC `0xFF0B` 2496×1872 1/124 `0x0820=0x0bd9` (#143). `0xFF03` was never WP VF. WOA 1/66 killed CCI. |
| Analog blob | Full CDCC idle (#68) **silenced** CSID. Subset `0xb04x` is daily #113. Leftover `0x69xx` (#151) still ECC. |
| SMIA supplies + Sony `0x4800` | ETL `0x0130/0132/0134` + `0x4800=0x0E` (#152). Stuck on the sensor; still ECC; irq storm froze UI. Do not keep. |
| CCI speed | WP Hill CCI1 ~1 MHz. Linux DT 100 kHz still ACKs. Not ECC. |
| CGC / MMCC / TCSR | #148 already matched WP VF CGC, phytimer 200 MHz, CSI0 266.67, MCLK 9.6, TCSR `0x9690e1`. |
| CAMIF geometry | WP VF 2496×1872. Linux HAL 4080×3028 is the **TG** size. Overflow when they disagree is not CSI. |
| VFE 320 MHz / CSI_VFE0 `0x4ff1` | After CSID. Do not flash 320 while CSI is broken. |

`long=0 map=0` is a red herring if ISPIF PIX SOF exists (TG path).

## WP dump facts (already used)

Hill viewfinder (Camera app, SensorMode **11**) is DCC **`0xFF0B`**:
2496×1872, WOI 4992×3744 origin 176,136, 2×2 bin, PLL 1/124, CSI
`0x0112=0x0A08` (RAW10 packed to 8-bit), `0x0820=0x0bd9` (DDR 379.2 MHz),
4-lane, settle 22, CSIPHY0, CSID0. Still snapshot is **`0xFF02`** (not
required for the ECC failure).

After software reset `0x0103` at SID `0x20`, WP writes supplies
`0x0130=0x0280` `0x0132=0x0133` `0x0134=0x01cd`, then **`0x0107=0x22`**
and almost all later I2C on SID **`0x22`**. Analog already sticks at
`0x20` on Linux. Do not `0x0107` without retargeting CCI SID (HAL stays
on `0x20` and would NACK). WP never writes `0x0500` compression. OIS is
a **different** slave **`0x7c`**. DCC blocks `0x0006` / `0xfe9b` /
`0xfe9c` are LSC/PDAF calibration, not CSI register maps.

Ghidra: rear KMD computes settle and hands CSIPHY properties off; it
does not poke CFG4/invert/`lane_assign`. CSID CORE/LUT/TG are written
in the rear SMIApp KMD (`CORE_CTRL_0 = 0x43203`, `CORE_CTRL_1` bit16,
TG **off** `0xa06436`, LUT DT `0x30`). Platform KMD is CCI + CGC mux.
ISP KMD is ISPIF/VFE **after** CSID.

A 2026-08-23 re-parse of the QcomCamera ETL, all 35 DCC blocks, live
KD MMIO, and KMD strings found **no unused CSI programming**.

Raw dumps stay local (`captures/`, gitignored). Do not publish ETL,
MainOS images, or WinDbg logs; they can identify a specific unit.

## What is still missing

These are not “one more register in the dumps”:

1. **Sharp `0xEACA` / Sony IMX230 D-PHY analog** under NDA. Public
   IMX230 trees are other modules. The WP idle analog table was
   applied in pieces; the full blob silences CSID.
2. **A scope** on CSI0 D-PHY (lane P/N, HS vs LP, which pad is clock).
   Schematic confirmation of CSI0 polarity would only re-check
   `pn_invert` / lane_assign, already swept.
3. **Front `0x2140` as a CAMSS control** (2-lane). Separate bring-up,
   not a Hill ECC fix.
4. **Sony register map** for packing vs DPCM. VF is `0x0A08` + CSID DT
   `0x30`; Linux crop table already writes `0x0A08`; LUT `0x30` still
   ECC.

A further WP dump of mid-shutter still MMIO would be `0xFF02` (595 MHz),
not the 379 MHz VF path.

## Do not bootloop / do not brick the bring-up

- Never `sensor_power_up` / `sensor_down` or `msm_sensor_platform_probe`
  from nested CCI `of_platform_populate`.
- Never disable PM8994 **LVS1** (shared 1.8 V VIO). Enable and hold.
- Never put LVS1 in `qcom,cam-vreg-name` / `power_setting`.
- MCLK (GPIO 13) then xshutdown, then `0x0103`. pinctrl name
  `cam_default` is **not** auto-selected; ident must select it.
- One `kzalloc` `s_ctrl` per node. DT `pdev->id_entry` is NULL.
- `CONFIG_VIDEO_SMIAPP` cannot bind these CCI children.
- Do not flash TG-auto-off kernels as daily. Do not flash
  `boot-smia93` (compat ioctl recurse), `boot-smia47` (CFG4=0),
  `boot-smia48` (WOA PLL), `boot-smia82` (CAMIF EFS killed SOF).
- Emergency Android: `out/boot-now.img` (kernel **#18**).
- After each flash read **`dmesg`**, not `logcat -b kernel` (stale pstore).

ACPI rail names: LVS1 = VIO, L23 = extra analog. snaccy’s
`lumia/camera.dtsi` **swaps** those names — do not copy that.

## Suggested next work (if any)

In order, only if new evidence appears:

1. Hardware: CSI0 D-PHY with a scope, or a Sharp/Sony register map for
   this module.
2. Front camera as a 2-lane CAMSS sanity check (new DT node, new
   bring-up). Do not mix with Hill TG kernels.
3. Userspace: chromatix / HAL3 after **live** CSI SOF exists. HAL1 is
   already proven on TG.

Do not start another CSIPHY CFG / lane_assign / CGC / `0x0107` flash
on the strength of the existing dumps.

## Tree layout

| Path | What |
|---|---|
| `dts/msm8992-talkman-camera.dtsi` | Three `qcom,smia65pp` nodes; Hill enabled |
| `kernel/smia65pp.c` | MSM wrapper + delayed SMIA++ ident. **Contains later CSI experiments** (including failed #152 supplies). Daily lab image was #113, not this file as-flashed. |
| `asl_files/camera.asl` | Talkman ACPI. Ignore `camera_mtp.asl`. |
| `scripts/apply-to-mmo-talkman.sh` | Copy DT/C into `android_kernel_mmo_msm8994` |
| `scripts/apply-csid-*.py` `apply-csiphy-*.py` `apply-vfe-*.py` | One-shot experiment patches. Read the header; many must never be re-applied. |
| `out/` | Magisk boot images (gitignored) |

Set `KERNEL_TREE` to the mmo kernel checkout. Set `ANDROID_SERIAL` for
`scripts/ocam-dump.py`. Do not swipe-up after Open Camera (that opens
Settings).

## Credits

Snaccy (`Android4Lumia950/android_kernel_msft_talkman` branch `smiapp`)
for the architecture. Nokia X2 `smia65pp` for the qcamera pattern.
Android4Lumia950 for the talkman kernel/ROM.
