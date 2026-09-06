# Talkman camera — working note

Read [`handoff.md`](handoff.md) first. This file is the short lab log.

## Now

Phone is on **`boot-smia113.img`** (**#131**, TG stays). Keep
`persist.camera.HAL3.enabled=0`.

**Dump audit (2026-08-23):** Re-parsed the 28.9 MB QcomCamera ETL (4249
internal writes, 2133 write16, 1315 CDCC, all SIDs), all 35
`0AEACA05.dcc` blocks, live KD MMIO (CSIPHY0–2 / CSID0 / CGC / CAMIF /
MMCC / TCSR / CCI / TLMM), and Ghidra rear/platform/core/ISP + driver
strings (front/iris/`ice5lp`). No unused CSI programming left. OIS is
SID **`0x7c`**. DCC `0x0006`/`0xfe9b`/`0xfe9c` are LSC/PDAF cal (not
addr/val maps). VF `0xFF0B` is CSI **`0x0A08`** (already in the crop
table). `0x0115=0x30` is the ident word `0x0114=0x0330`, not a DT
knob. Still-mode MMIO was never caught; it would be `0xFF02`, not ECC.

**#152** (`boot-smia152.img`, **#170**): SMIA voltages + Sony `0x4800`
**stuck** (`0130=0x280` `0132=0x133` `0134=0x1cd` `4800=0xe`). After
12s TG-off still ECC (`pkts=0xff3bee ecc=0xffff`, irq `0x100100dd`).
CSID irq **storm** (~180k suppressed / 5s) froze the UI; IOMMU FAR
`0x8e000`; CAMIF `st=0x13f8` (4080 TG vs 2496). Pink/green is TG, not
a scene. Supplies/0x4800 are not the CSI gap. No further non-lottery
CSI flash.

**#151** (`boot-smia151.img`, **#169**): analog leftover stuck
(`3121=1` `6962=0x3a` `69bc=5` `b040=0x90`). `wpmap` `0112=0xa08`
`0820=0xbd9`. After TG-off still **`0x20000dd ECC`**. First OC open
froze at I2C #5; retry streamed. CAMIF `st=0x13f8` (4080 TG vs 2496).
Do not keep as daily (TG-off). Analog 0x69xx is not the CSI gap.

**ETL unused (do not recapture writes):** After `0x0103` at SID `0x20`, WP
writes SMIA supplies **`0x0130=0x0280` `0x0132=0x0133` `0x0134=0x01cd`**
(8.8 V: 2.50 / 1.20 / 1.80), then **`0x0107=0x22`** and the rest on SID
`0x22`. Linux never writes those. Also Sony global **`0x4800=0x0E`**
(public `imx230.c` same value) plus `0x4890`/`0x4d1e`/`0x4fa0`/`0x6153`/
`0x7300`/`0x9009`. Do **not** `0x0107` without retargeting CCI SID (HAL
would NACK `0x20`). Do **not** `0x0500` (WP never writes it). Do **not**
replay the 0x9xxx idle blob (#68). **#152 wrote voltages + `0x4800`;
still ECC.** Do not repeat.

**ETL I2C (already on disk):** Hill analog goes out CCI SID **`0x22`**
(`0x20` is reset / voltages / `0x0107` / `0x0136`). VF `0x0100=1`,
`0x0820` high **`0x0b`** (`0x0bd9`), `0x0111=2`, bin `0x0900=1`.
`0x0808` never written. `0x3150-0x3156` is **3A** — do not static-write.
Idle `0xb04x` matches #113. #151 leftover `0x69xx` stuck, still ECC.

**WP VF 2026-08-22-cci:** CCI live `00=0x10020001`. Hill **CCI1 ~1 MHz**
(`SCL thigh=16 tlow=22`). Linux DT is 100 kHz; not the ECC gap. Do not
dump CCI again (driver `CCI IRQ EXPIRED`). CSIPHY0 5-lane CFG
`0x3f/0x16/0xff/0x22`. TLMM VF GPIO13 `0x284`, 19/20 `0x204`, 91/92 `0x1`.
CSID/CAMIF unchanged. WP MMIO session **done**. Analog `0x69xx` was
#151 and is not the CSI gap. **#152** voltages/`0x4800` stuck, still
ECC + irq storm. Restore 113. No more CSI lottery.

**#150** (`boot-smia150.img`, **#168**): TG DT **`0x30`** into WP LUT.
Wrote (`dt1=0x30`). TG-on **`map=0 unmap=0`**, ecc tracks pkts. #149
`0x2B` TG had **`unmap=0x2b221322`** (valid headers, wrong DT). TG
does not emit usable DPCM `0x30` packets — not a HAL paint proof.
After 12s off still **`0x20000dd ECC`**. Screencap timed out (USB).

**#149** (`boot-smia149.img`, **#167**): TG **4080×3028**. TG-on irq
**`0x8010200`**. Stats **`unmap=0x2b221322`**: DT **`0x2B`**, LUT **`0x30`**.
After TG-off still **`0x20000dd ECC`**.

**#148** (`boot-smia148.img`, **#166**): live Linux CAMSS already **matched
WP VF CGC** before the poke (`00=0x60010000` `10=2` mux 0, enables
`0xf/0x3f/3/3/3`). PHYTIMER `0x107`, CSI0 `0x105`, MCLK `0x3`, TCSR
`0x9690e1` match. Leftover MMIO: CSI_VFE0 **`0x6ff1` vs WP `0x4ff1`**,
VFE0 **`0x501` 600 MHz vs WP `0x104` 320**. After TG-off still
**`0x20000dd ECC`**. `0x0100=1` at table 8 *before* TG-off. CGC is not
the ECC gap.

**#147** CSI0 266.67 wrote (`now=266670000`). Still ECC.

**#146** WP CID LUT `0x30`/`0x51`. Still ECC, `map=0`. LUT is not an ECC
fix. Ghidra “LUT DT0 `0x2b`” was the code default, not live VF.

**#145** 2496 TG: overflow gone; TG-on already ECC. Daily pink is 113.


CSID 3.0 irq: `0x02000000` = **ECC**. 4-lane after TG-off is ECC. Grey
OC = restart daemons.

**#112** (`boot-smia112.img`, **#130**): WP TG_CTRL idle `0xa06436` from
the start + `0x0100=1` at I2C table 1. HAL still `WRITE_I2C #5` then
`type=6` (CFG_POWER_DOWN) at 5s. CSID never configured. Open Camera
FAILED TO OPEN CAMERA. Early `0x0100` makes HAL wait for a frame before
CSI. Do **not** repeat.

**#113** (`boot-smia113.img`, **#131**): CDCC idle `0xb040`–`0xb077` +
`0x31e0/31e1/69bb`, skip `0x0136/0137/0138`. Analog stuck (`b040=0x90`).
TG stays. Pink preview. Analog expansion does not silence CSID.

**#114–#119**: TG-off CORE_CTRL sweep. Clock phy1. Table below.

**#120** (`boot-smia120.img`, **#138**): after-off `0x2430` → `0x20000dd`.

**#121** (`boot-smia121.img`, **#139**): after-off `0x2340` → `0x20000dd`.

**#122** (`boot-smia122.img`, **#140**): sensor `0x0114=1`, CSID `0x201`.
Irq **`0x2000cc` / `0x200000`**. First useful PHY signature.

**#123** (`boot-smia123.img`, **#141**): CSIPHY `mask=0x7`. Same `0x2000cc`.

**#124** (`boot-smia124.img`, **#142**): `pn_invert=3` data-only. Same.

**#125** (`boot-smia125.img`, **#143**): 2-lane `0x40` + `mask=0x13`.
**No CSID irq** after TG-off (silent). Wrong pair.

**#126** (`boot-smia126.img`, **#144**): colorbars `0x0600=2` + 2-lane
`0x20`. Still `0x2000cc`. Sensor test pattern does not decode.

**#127** (`boot-smia127.img`, **#145**): `0x0138=1` wrote. Still `0x2000cc`.

**#128** (`boot-smia128.img`, **#146**): `0x0808=0` (DPHY auto). Still
`0x2000cc`. Restored 113.

**#129** (`boot-smia129.img`, **#147**): 4-lane + extclk `0x0136=0x0999`.
After TG-off **`0x20000dd ECC`**. 2-lane was PHY_OVR. Restored 113.

**#130** (`boot-smia130.img`, **#148**): mainline 1× `0x0820=0x01b02100`
stuck + extclk `0x999`. Still **`0x20000dd ECC`**. Restored 113.

**#131** (`boot-smia131.img`, uname **#149**): skip `0x0820` + extclk
`0x999`. Still **`0x20000dd ECC`**. `boot-smia131.img` is **not** daily
uname #131 (`boot-smia113.img`). Restored 113.

**#132** (`boot-smia132.img`, **#150**): CSIPHY CFG5 `0x52→0` (EQ off).
Wrote and stuck. Still **`0x20000dd ECC`**. Restored 113.

**#133** (`boot-smia133.img`, **#151**): `test_imp` `0x17→0x10` + CFG5=0.
Still **`0x20000dd ECC`**. First dump USB-dropped; 133b streamed. Restored
113.

**#134** (`boot-smia134.img`, **#152**): `CORE_CTRL_1 or=0x10009`.
`ctrl1=0x10009` stuck. After TG-off still **`0x20000dd ECC`**. Restored
113.

**#135** (`boot-smia135.img`, **#153**): `0x0808=2` REGISTER + UI timings
in one group. **`now=0x2` stuck**, `post=0x0` (0x0800 did not take).
Still **`0x20000dd ECC`**. Restored 113.

**#136** (`boot-smia136.img`, **#154**): `0x0808=2` first, then
`0x0800–0x0807`. **`now=0x2`**, all timings still **0**. REGISTER timing
regs are not writable on EACA. Still ECC. Restored 113.

**#137** (`boot-smia137.img`, **#155**): idle `0x31a8=0x18` stuck. Still
**`0x20000dd ECC`**. Restored 113.

**#138** (`boot-smia138.img`, **#156**): `0x0820` WP lane 106.2 Mbps
stuck `0x006c0840`. UI timings still 0. Still **`0x20000dd ECC`**.
Restored 113.

**#139** (`boot-smia139.img`, **#157**): CSIPHY CFG4 `0x5→0xff` CFG5
`0x52→0x22` stuck. After TG-off still **`0x20000dd ECC`**.

**#140** (`boot-smia140.img`, **#158**): CFG2 `0x10→0x3f` stuck.
`+0x2c` already **`0x70`** (no write). Still ECC.

**#141** (`boot-smia141.img`, **#159**): CFG3 `0x23→0x16` stuck. CSIPHY0
lane dump matches WP live. Still ECC.

**#142** (`boot-smia142.img`, **#160**): DCC `0xFF03` 2672×1504 PLL
1/120 stuck. `0x0100=1`. After TG-off still ECC.

**#143** (`boot-smia143.img`, **#161**): DCC `0xFF0B` 2496×1872 PLL
1/124 `0x0820=0x0bd9` stuck (`wrc=0`, `dt=0xa08`). After TG-off still
**`0x20000dd ECC`**. Pink TG preview. HAL CAMIF still 4080×3028.

**#144** (`boot-smia144.img`, **#162**): CAMIF 2496×1872 full window.
Overflow `0xff8` while TG is 4080. After TG-off still ECC.

**#145** (`boot-smia145.img`, **#163**): TG 2496×1872. Overflow gone.
TG-on irq `0x2000200 ECC`. After TG-off still `0x20000dd`.

**#146** (`boot-smia146.img`, **#164**): WP CID LUT `0x30`/`0x51`. Still
ECC, `map=0`. LUT is not an ECC fix.

**#147** (`boot-smia147.img`, **#165**): CSI0 266.67 MHz. Still ECC.

**#148** (`boot-smia148.img`, **#166**): CGC enables already matched WP.
TCSR/phytimer/CSI0/MCLK match. Still ECC. CSI_VFE0 `6ff1` vs `4ff1`.

**#149** (`boot-smia149.img`, **#167**): TG 4080. Unmap shows DT `0x2B`.
After TG-off still ECC.


| assign | clk | irq after TG-off |
|---|---|---|
| `0x4320` | phy1 (WP) | **`0x20000dd`** (#114) |
| `0x4321` | phy0 | `0xe000dd` (#115) |
| `0x4310` | phy2 | `0xd000dd` (#116, clock-as-data) |
| `0x4210` | phy3 | `0xd000dd` (#117) |
| `0x3420` | phy1, data swap | `0x80000dd` (#118) |
| `0x4230` | phy1, data swap | `0x20000dd` (#119) |
| `0x2430` / `0x2340` | phy1, 4-lane permute | `0x20000dd` (#120/#121) |
| `0x20` 2-lane | phy1, data 0+2 | **`0x2000cc` / `0x200000`** (#122) |
| `0x40` 2-lane | phy1, data 0+4 | silent (#125) |

## Proven (do not rediscover)

- Snaccy: SMIA++ + Nokia `qcom,smia65pp` + HAL name **imx230**. Hill first.
  One `s_ctrl` per node. Repo `smiapp` branch. `camera.asl` not MTP.
  `ice5lp` = UC120, not camera.
- Ident: ACPI L23+L29+L25+LVS1, `cam_default` pinctrl (GPIO 13 = MCLK),
  MCLK then xshutdown, `0x0103`. Never disable LVS1. Never `sensor_power_up`
  at init. Never `msm_sensor_platform_probe` during CCI populate (#4).
- Delayed `msm_sensor_platform_probe` after ident: subdev registers, no
  bootloop (#15). Bind that `s_ctrl` into `g_sctrl[cell-index]` (#16) so
  bullhead `CFG_SINIT_PROBE` takes the already-probed path. Do **not** add
  `qcom,camera` on the same CCI/GPIOs.
- WP rear KMD: `cam_drv_0AEACA_*`, I2C **1 MHz**, 4-lane CSI, then CDCC/NVM
  + `SMIApp_StartStream` (that is HAL, not kernel).
- CSI DT: `lane-assign 0x4320` / `mask 0x1F`. No `cam_vio` in cam-vreg-name.
- Daemon XML list: line **274** = missing `.so`. Line **323** = lib loaded,
  kernel probe failed. No imx230 error after slot bind + daemon restart.
- Magisk lib: `su -M`, **0644** `vendor_file`, never bind from `/sdcard`.
- Open Camera “1 camera, Failed to start preview”: ISP ioctl size, not
  missing sensor. #34 `INPUT_CFG` 148 vs 144. #36 `CFG_STREAM` matched.
  #37 CPP `num_buffs==0` matched. Then SOF freeze.
- Sensor ioctl `argp` is a **kernel** pointer (`video_usercopy`). Do not
  `copy_from_user` it (#39 → 0 cameras).
- Hill DATA_TRANSFER_IF_1 page 0 works (`stat=0x1`). Module has NVM.
- Open Camera swipe-up opens Settings. Dump script must not swipe after launch.
- 20nm CFG4 is **writable**. Reset 0x5. Bit 2 must stay set or CSID goes
  silent. Bit 0 is not a working P/N invert.
- **CAMIF (VFE44):** ISPIF PIX SOF ~37 fps. CAMIF SOF lockstep, **never
  EOF**. HAL 4080×3028, **pixclk 424.8 MHz**, hbi=0. ppl **4088** clears
  overflow `0xff8`. 1-line window → `0xbd40000` = **3028 lines**. 0x31C is
  an error latch (0 mid-frame). **#92 200 MHz overflow `0x15f8`=5624 px
  proves pixels reach CAMIF.** Revert 200 MHz; next 480/600 MHz or HBI.
  See [`notes/camif.md`](camif.md). Isolate `0x0100=0` stays on.

## Failed

| Try | Result |
|---|---|
| power_up/down at init | bootloop #1–#3 |
| platform_probe at CCI populate | bootloop #4 |
| xshutdown before MCLK | NACK #9 |
| clock on, GPIO 13 unclaimed | NACK #13 |
| bullhead IMX377 as the sensor name | snaccy: wrong identity |
| bind `libmmcamera_imx230.so` from `/sdcard` | dlopen fails (noexec/sdcardfs) |
| `killall` daemon without `su -M` | wrong mount ns; old PID stays |
| `su -M` on `/data/adb/modules` | permission denied; omit `-M` there |
| qcamerasvr at ~6s, ident at ~9s | first probe -22; restart daemon after ident |
| #34 Open Camera preview | Invalid ISP `INPUT_CFG` size 148 |
| #35 Open Camera preview | Invalid ISP `CFG_STREAM` size 36; CPP num_buffs=0 |
| #36 Open Camera preview | CFG_STREAM OK; CPP `Invalid number of buffers`; SOF freeze |
| #37 Open Camera preview | CPP STREAMON OK; SOF freeze (no CAMIF frame) |
| #38 Open Camera preview | CSIPHY OK; CSID IRQ `0x20000dd` storm; no START_STREAM |
| #42 Open Camera preview | 4080 + `0x0100=1` + PLL 4/177; CSID `0x20000dd`; SOF freeze |
| #43 Open Camera preview | WOA PLL then `0x0100` on table #1; CCI 0; CSID `0x800` |
| #47 Open Camera preview | `0x0111` write does not stick (`sig=0x2`); still ECC |
| #48 Open Camera preview | `0x3210` pkts=0, IRQ `0xd000dd` (clock mapped as data) |
| #49 Open Camera preview | `0x0234` same as #47: pkts+ECC |
| #50 Open Camera preview | settle `0x28`; still pkts+ECC |
| #51 Open Camera preview | DPHY_CTRL=UI, `0x0820=0`; still ECC |
| #52 Open Camera preview | `0x0820=0x01b02100` sticks; still pkts+ECC |
| #53 Open Camera preview | `0x0820=0x03604200` sticks; still pkts+ECC |
| #54 Open Camera preview | colour bars `0x0600=2` stuck; still ECC |
| #55 Open Camera preview | DPHY_CTRL auto `now=0`; timings 0; still ECC |
| #56 Open Camera preview | `max4=1500 Mbps/lane`; NVM IF idle; still ECC |
| #57 Open Camera preview | NVM page0 real; same CSID pkts+ECC |
| #58 Open Camera preview | CSIPHY `lnn_misc1` bit 0 invert; same ECC |
| #59 Open Camera preview | CSID `0x4302` ln0=phy2; same ECC |
| #60 Open Camera preview | CSID `0x4203` ln0=phy3; same ECC |
| #61 Open Camera preview | CSIPHY dump; cfg4=0x5 cfg5=0x52; viewfinder black |
| #62 Open Camera preview | late irq 0x4 all lanes; cfg4/5 unchanged; still ECC |
| #63 Open Camera preview | half CSI `op_sys=2`; same ECC + irq 0x4 |
| #64 Open Camera preview | CFG4 `0x5→0x4` stuck; still pkts+ECC |
| #65 Open Camera preview | CFG4=0; PHY irq 0x4; **CSID silent** |
| #66 Open Camera preview | WOA 1/66 at table 7; CCI 0x01; CSID silent |
| #67 Open Camera preview | CDCC 1/124 stuck; CCI ok; PHY irq 0x4; **CSID silent** |
| #68 Open Camera preview | CDCC idle on 4/177; CCI ok; PHY irq 0x4; **CSID silent** |
| #69 Open Camera preview | idle then 1/124; CCI ok; PHY irq 0x4; **CSID silent** |
| #71 Open Camera preview | CDCC override 0x1bxx; readback 0; pkts+ECC; `long=0` |
| #72 Open Camera preview | CSIPHY data-only invert; same pkts+ECC |
| #73 Open Camera preview | CSIPHY clock-only invert; same pkts+ECC |
| #74 Open Camera preview | WP CSID CORE_CTRL_1 `0x1000F`; same pkts+ECC; MISR live |
| #75 Open Camera preview | CSID TG 4080×3028 `0xa06437`; CORE_CTRL skipped; CSID silent |
| #76 Open Camera preview | TG+CORE_CTRL; TG pkts before 0x0100; ECC low-half; still black |
| #77 Open Camera preview | skip 0x0100 at table 7; HAL table 8 streamed anyway; TG-only no 0xdd |
| #78 Open Camera preview | force 0x0100=0; isolate holds; TG SOF IRQs; no 0xdd; still black |
| #79 Open Camera preview | TG_VC num DT=3 (`0x8080000c`); still `long=0`; ECC high-half too |
| #80 Open Camera preview | CAF num DT=0 + payload 0x55/0xAA; SOF IRQs; `long=0`; still black |
| #81 Open Camera preview | TG CORE_CTRL without `0x4320`; IRQ `0x2000000`; no SOF |
| #82 Open Camera preview | restore 0x4320 + dump map 0x70; `long=0 map=0`; still black |
| #83 Open Camera preview | TG DT0 pixels 4080 (`0xff00bd4`); IRQ `0x2000000`; SOF gone |
| #85 Open Camera preview | ISPIF PIX SOF ~37 fps; **CAMIF error 0xff8**; still black |
| #86 Open Camera preview | CAMIF SOF yes, **EOF never**; clk=480MHz; st=0xff8 (4088 px line 0) |
| #87 Open Camera preview | ppl 4088 **cleared CAMIF error**; still **never EOF**; black |
| #88 Open Camera preview | CAMIF 1-line; error **0xbd40000 = 3028 lines**; still no EOF |
| #89 Open Camera preview | full window 0..4087×0..3027; **no error, still never EOF** |
| #90 Open Camera preview | 0x31C **st=0x0 at every SOF**; s1=0; still no EOF |
| #91 Open Camera preview | mid-frame **st=0x0** cmd=1 cfg=0x40 extra=`0xaadc0000`; no EOF |
| #92 Open Camera preview | pixclk 200 MHz; error **0x15f8=5624 px**; **pixels live**; no EOF |

## Restore

`boot-smia113.img` = **#131** current HAL1 TG preview (idle `0xb04x` analog, TG stays).
`boot-smia109.img` = **#127** analog subset, TG stays.
`boot-smia108.img` = **#126** TG stay, no analog.
`boot-smia101.img` = **#119** first HAL1 pink viewfinder (0x0100 isolated).
`boot-smia95.img` = **#113** last AXI+SOF+subscribe log (HAL type 0x1ff).
`boot-smia92.img` = **#110** AXI + kernel SOF send (HAL never DQEVENT).
`boot-smia89.img` = #107 AXI without IOMMU.
`boot-smia86.img` = #104 CAMIF SOF+EOF, drop=0, no AXI DMA.
`boot-smia44.img` = CSI-class restore (#62).
`boot-now.img` = kernel **#18** if Android dies.
Do **not** flash `boot-smia105/106/107/110/111/112/114/115/116/117/118/119`
(TG auto-off / never-TG freeze / lane-sweep samples).
`boot-smia119.img` is uname **#137**, not the first HAL1 (`boot-smia101` **#119**).
Do **not** flash `boot-smia120`–`boot-smia152` as daily (TG auto-off CSI samples).
`boot-smia131.img` is uname **#149**, not daily #131.
Do **not** flash `boot-smia93.img` (#111 recurse bootloop).
Do **not** flash `boot-smia96.img` (#114 ALL=-EINVAL).
Do **not** flash `boot-smia97.img` / `boot-smia98.img` (subscribe remap, table-12).
Do **not** flash `boot-smia82.img` (#100 EFS, killed CAMIF SOF).
Do **not** flash `boot-smia47.img` (#65 CFG4=0), `boot-smia48.img` (#66 WOA),
`boot-smia65.img` (#83 pixel DT0), `boot-smia70.img` (#88 1-line),
`boot-smia74.img` (#92 200 MHz), `boot-smia75.img` (#93 320 MHz).
