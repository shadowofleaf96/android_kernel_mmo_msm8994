# Ghidra: WP Hill CSI / CSIPHY

`captures/` is gitignored.

## Done: rear SMIApp KMD

Export:

```
captures/wp-83268-camera/ghidra/Decompile_Output/
  qccamrearsensor_primarySMIApp8992.sys.c
  qccamrearsensor_primarySMIApp8992.sys.h
```

Import that worked: PE **ARM:LE:32:v8:windows** (`machine 0x1C4`, PE32). Not AARCH64.

This file **does not** write CSIPHY analog (no CFG4/CFG5/misc1, no invert, no `lane_assign` / `0x4320`). It computes CSI properties and hands them off.

### Settle (the wiki log formula)

When the sensor is CSI-2 (`*(obj+0x6c) == 3`):

```
PHYTIMER = 200e6 Hz on 8992   // chip IDs 0xa/0xb use 177.78e6 instead
DDRClk   = SensorMode.DDRClk  // Hz; 0 is forced to 1
settle   = (int)(((4e9 / DDRClk + 100.0) * PHYTIMER) / 1e9 + 0.5)
```

That is stuffed into `MIPICsiPropSettleCount` (blob +0x10). Lanes go in byte 0, DDRClk Hz at +0x20. Then it logs `[CSIPHY Config] ID = %d, PHY default mode %d lanes` (combo 2+1 only if a flag is set).

`FUN_004010bc` is uidiv(divisor, numerator). DDRClk from SMIA feedback:

```
bpp    = 10 for RAW10 (8 if format 1 or 7, 6 if format 4)
DDRClk = ((op_pix_khz * bpp / lanes) >> 1) * 1000
       = op_pix_hz * bpp / (2 * lanes)
```

Live Hill EACA PLL 4/177 @ 9.6 MHz: `op_pix = 42.48 MHz`, 4-lane RAW10 → **DDRClk = 53.1 MHz** (106 Mbps/lane). Settle at 200 MHz PHYTIMER ≈ **35 (`0x23`)**.

Wiki `MIPIDDRClock=633600000` / settle 21 is a **different mode** (matches RAW8 with `op_pix ≈ 633.6 MHz`). Not this Sharp module’s native PLL. Do not apply WOA 1/66 (#66 already killed CCI).

Linux `use=200000000` is the same PHYTIMER clock, not MIPI DDR. HAL settle `0x1b` and our force `0x28` already bracket WP’s `0x23`; do not flash settle-only for this.

### Lanes / PLL / signalling

- Registry `CameraCSI\MaxCsiLanes` default **4** → `CSI2_lane_mode = 3` → SMIA `0x0114` write. Matches us.
- Ext clock default **9.6 MHz**. I2C 1000 kHz if `CameraI2C\I2cFreqKhz=1000`.
- `MaxCsiFreqMhz` default `0x28a` (650) → `requested_link_bit_rate_mbps = 1300`.
- PLL regs `0x0300`–`0x030F` come from CDCC/DCC mode blocks, not a hardcoded 1/66.
- `0x0111` / `0x0114` written in `cam_drv_SMIApp_sensor_config` from capability bits + requested lane mode.

### CSI clock mux

Sensor activate calls platform `IOCTL_KMD_CAMERA_PLATFORM_CSI_CLK_MUX_CONFIG` (`0x232027`). That ioctl lives in `qccamplatform8992.sys`. PHY already HS-locks on Linux, so this is not the first knob; still the next decompile.

## Done: platform KMD (`qccamplatform8992.sys`)

Export:

```
captures/wp-83268-camera/ghidra/Decompile_Output/qccamplatform8992.sys.c
```

Same PE32 ARMNT. Ghidra C missed the PVT ioctl jumptable at **`0x0040261c`** (`tbh`; base ioctl `0x232003`). Recovered from `.pdata` + Thumb.

This file is CCI + gyro + power + **CSI clock mux**. It does **not** write CSIPHY CFG3/4/5, misc1, invert, or CSID `lane_assign`. Mapped CAMSS BARs (`DAT_0042361c` / `c5a4` / `c520`) are never used for analog PHY in the decompile.

### CSI clock mux (real WP behaviour)

Sensor calls ioctl `0x232027` (8-byte buffer). Handler is **`0x232025`** at `0x402a98` (method bits). Release is `0x232029`.

Input: dword0 = mux 0..3, dword1 = VFE interface bitmask.

| mux | CSI clocks (0x10 = list end) |
|-----|------------------------------|
| 0 | `0xa`, `0xb` |
| 1 | `0xc`, `0xd` |
| 2 | `0xe` |
| 3 | `0xf` |

VFE mask bits then append clocks 6..9 and 0..5. Mux > 3 → `Invalid mux selection`. Preferred VFE in bits 30–31 must be 0 or 1.

`FUN_0040854c` claims those clock IDs. `FUN_004082b4` writes 2-bit CGC selects to `CAMSS_BASE+0x20/0x28/0x30/0x38/0x40`. `FUN_00408400` writes enable bits at `+0x24/0x2c/0x34/0x3c/0x44`. Hill path is mux 0 (ACPI CSI0). Linux already enables `camss_csi0*` clocks; this is not analog PHY.

`CAMSS_GetBase` (`FUN_004086e8` → `FUN_00408ec4(3)`) only logs the MMIO base used for those CGC regs. Chip ID map is `0xfd510000+0x2028` / `0xfd480000+0x28000`.

## Done: core KMD (`qccamcore8992.sys`)

Full export (11 MB C) is enough. Those CSID strings are **diagnostics / property copy**, not PHY analog.

- `ReadCsiRegisters` / SelfTest: ioctl **0x53**, 16 bytes: `receivedPackets`, `crcErrors`, `eccErrors`. Same CSID stats we already dump.
- `CtlConfigCSIDInterface_Sensor`: ioctl **0x4f**, **4-byte** `m_CSIDType` get then set. No lane map, no LUT.
- `CtlInfoISPIF_Sensor`: ioctl **0x11**, **0x240** blob, 12 channels × `{nCSIDIndex, nCID, PIDataRate, outputInterface, rdiInterface, frame W/H, csiDT, stereo}`. Filled by the **sensor** KMD (rear ConfigResolution), not computed here.
- Init: `GetISPIFInfo` (sensor vtable +0x54) then `ConfigureCsiClockMuxes` (vtable +0xe4 → platform CGC mux we already have).
- RDI path logs `csiDT` and writes lane mask **`0x1f`** (same as our DT).

No CSIPHY, invert, or `lane_assign` in core. CSID MMIO is **`qccamisp8992.sys`** (`ISPIF_CMD_ID_CFG`).

## Done: ISP KMD (`qccamisp8992.sys`)

Export:

```
captures/wp-83268-camera/ghidra/Decompile_Output/qccamisp8992.sys.c
```

Source name in the binary: `CameraISPIFHAL.c`. **Zero CSID/CSIPHY strings.** This is ISPIF + VFE + CPP, **after** CSID has already decoded packets. It cannot explain uncorrectable CSID ECC.

`ISPIF_CMD_ID_CFG` (cmd **0x1f7**, 0x28-byte blob) / `ISPIF_CMD_ID_INTF_CFG` (**0x1f8**, 0x24 bytes) → `DAL_ispif_intf_cfg` → `HAL_ispif_intf_cfg` (`FUN_0046bf44`):

| MMIO (per VFE, stride **0x200**) | What |
|---|---|
| `ISPIF_BASE+0x244` | CSID index in 2-bit fields (PIX bits 1:0, RDI0 <<4, RDI1 <<12, RDI2 <<20) |
| `+0x254` | PIX CID mask (16 occupancy bits) |
| `+0x264 / +0x268 / +0x26c` | RDI0/1/2 CID masks |

Interface ids: PIX=1/2, RDI0=`0x10`, RDI1=`0x20`, RDI2=`0x40`. Same layout as Linux `msm_ispif`. Lane mask **0x1f** already matches us. No invert, no CFG4. CSID **is** programmed in the **rear SMIApp** KMD (`FUN_0041ddd4` / `FUN_0041da00`), not in `qccamisp`.

## Done: CSID MMIO in rear SMIApp (`FUN_0041ddd4`)

Not a missing KMD. Rear writes CSID 3.0 MMIO (`DAT_00832060+4/8` = CORE_CTRL_0/1):

| | WP live | Linux 3.10 msm_csid |
|---|---|---|
| CORE_CTRL_0 | `(lane_cnt-1) \| (nibbles << 4)` default **0x43203** (`lane_assign 0x4320`) | same (`0x4320`) |
| CORE_CTRL_1 | `phy_sel << 17 \| **0x1000F**` | `phy_sel << 17 \| **0xF**` |
| TG_CTRL | **0xa06436** (disable) | never written |
| LUT DT0 | live **`0x30`** (user-defined), not code default `0x2b` | Linux HAL `0x2b` RAW10 |

Init default `0x32103` is overwritten before the MMIO write. `#48` `0x3210` is that unused default, not live WP. `0x4320` in `qccamcore` is a float (`20 43 00 00`), not a lane map.

After TG-off, rewriting CORE_CTRL_0 (Linux TG used `0x43203`) changes CSID irq, so the PHY path is live and mapped:

| CORE_CTRL_0 | assign | meaning | irq |
|---|---|---|---|
| `0x43203` | `0x4320` | WP, clk phy1 | `0x20000dd` |
| `0x43213` | `0x4321` | clk phy0 | `0xe000dd` |
| `0x43103` | `0x4310` | clk phy2 | `0xd000dd` |
| `0x42103` | `0x4210` | clk phy3 | `0xd000dd` |
| `0x34203` | `0x3420` | clk phy1, data 3↔4 | `0x80000dd` |
| `0x42303` | `0x4230` | clk phy1, data 2↔3 | `0x20000dd` |
| `0x24303` | `0x2430` | clk phy1, data permute | `0x20000dd` (#120) |
| `0x23403` | `0x2340` | clk phy1, data permute | `0x20000dd` (#121) |
| `0x201` | `0x20` 2-lane, clk phy1 | **`0x2000cc` PHY_OVR** (#122) |
| `0x401` | `0x40` 2-lane, phy 0+4 | **silent** (#125) |

`0xd000dd` matches `#48` (clock mapped as data). Clock is phy1. 4-lane
data permutes of `{0,2,3,4}` do not get SOF. 2-lane `0x20` (phy 0+2) is
the live pair; `0x40` is not. 2-lane irq is **PHY DL overflow**, not
ECC — do not use 2-lane at 4080 for scene. Color bars still fail. #129
extclk 16.8 on 4-lane: still **`0x20000dd ECC`**.

Bit 16 of CORE_CTRL_1 (`0x10000`) is the only CSID word WP sets that Linux did not. **#74** applied it (`ctrl1=0x1000f`): same pkts+ECC, `long=0`; **MISR became live** (was 0). Treat bit 16 as MISR enable, not a header-ECC fix.

**#75** CSID TG (`0xa06437`, 4080×3028, dt `0x2b`, skip CORE_CTRL like CAF 7.1): enable logged, then CSID **silent** (`0x800` only). PHY still HS-locks. Next TG try: keep CORE_CTRL writes.

Do not decompile front/iris/`ice5lp` for analog PHY. CSID test generator (`0xa06437`) is Linux-only; WP never enables it.

## Original-driver data: CDCC `.dcc` (not another KMD)

Rear KMD loads `\SystemRoot\System32\Drivers\<id>.dcc`. Live Hill `0x0002=0x050A` → **rev 5** → **`0AEACA05.dcc`**.

Extracted from `captures/wp-83268-camera/36.MainOS.ntfs` (scripts `_extract_dcc.py`):

```
captures/wp-83268-camera/dcc/0AEACA05.dcc   (rev 5, 1.72 MB)
0AEACA01/02/04/11/12/14/15.dcc
0A214000.dcc / 0A214001.dcc   (front)
```

Format **0x1f**, 35 sub-blocks. Mode 0 (id `0xff00`) is WP’s native still:

| | Ident (reset) | CDCC mode 0 |
|---|---|---|
| window | 5344×4016 | **5344×3744** (y start 136) |
| `0x0112` | 0x0A0A RAW10 | 0x0A0A |
| `0x0114` | 3 (4-lane) | 3 |
| pre / mult `0x0304/06` | 4 / 177 | **1 / 124** |
| vt `0x0302/00` | 2 / 4 | **2 / 5** |
| op `0x030A/08` | 1 / 10 | **1 / 10** |
| `0x0310` | — | **1** |
| `0x0820` | 0 | **0x1299** (bytes `0x12`,`0x99` only) |

9.6 MHz × 124 / 1 → VCO **1190.4 MHz**, vt **119.04**, op_pix **119.04**, DDRClk ≈ **148.8 MHz**. Wiki 633.6 MHz / 1/66 is a **different** mode. #66 1/66 stays forbidden.

**#67** applied PLL+`0x0820` only (kept 4080 crop). Writes stuck. CCI alive. CSID went **silent** (`0x800`). Ident 4/177 is still the only PLL that produces CSID packets. Do not leave 1/124 as default.

Idle `0x0136/0137 = 0x09,0x99` is SMIA 16.8 **9.6 MHz** (`ext_clk / (1e6/256)` = `0x0999`), **not 9.99**. #129 wrote it; 4-lane still `0x20000dd ECC`. Full idle (#68) silenced CSID for other regs.

CSID 3.0 IRQ (CAF 2.x/3.0 headers, confirmed live #129): `0x02000000` ECC, `0x01000000` CRC, `0x00F00000` PHY DL overflow. 4-lane after TG-off is **ECC**. 2-lane `0x00200000` is **PHY_OVR** — not a scene path.

Idle `0x0138` is SMIA **TEMP_SENSOR_CONTROL**, not DPHY clock. Do not flash it as CSI.

20nm Linux never writes `LNn_CFG5` (offset 0x10). Linux Open Camera
left **CFG4=`0x5` CFG5=`0x52`**. That is the **idle** PHY (WP CSIPHY1/2
look the same). **#132** CFG5→0 and **#133** `test_imp` 0x17→0x10 were
the wrong direction.

## Live WP MMIO (2026-08-22, Camera preview, KD `dd /p`)

Raw: `captures/wp-83268-camera/kd-camss-mmio.txt`.
CSID1+ / ISPIF / VFE are `????????` after USB drop + watchdog reboot
in Break — ignore those. CSIPHY0–2 and CSID0 are good.

20nm stride **0x40**/lane. Hill is **CSIPHY0** `0xFDA0AC00` (pwr `0x3f`).
CSIPHY1/2 are idle (pwr 0, CFG4=`0x5`, CFG5=`0x52`).

| Off | Linux (#139 dump) | WP live lane 0–4 |
|---|---|---|
| +0x04 CFG2 | **`0x10`** | **`0x3f`** |
| +0x08 CFG3 | **`0x23`** (settle) | **`0x16`** |
| +0x0c CFG4 | **`0xff` stuck** (was `0x5`) | **`0xff`** |
| +0x10 CFG5 | **`0x22` stuck** (was `0x52`) | **`0x22`** |
| +0x1c test_imp | **`0x17`** | **`0x17`** (match; do not change) |
| +0x28 misc1 | **`0,4,28,18,8`** (already match) | `0, 0x4, 0x28, 0x18, 0x8` |
| +0x2c | not dumped | **`0x70`** all live lanes |

CSID0 `0xFDA08000` matches Ghidra CORE; **CID LUT does not match Linux HAL:**

| Off | WP live VF | Linux HAL (#143) |
|---|---|---|
| +0x10 LUT_VC_0 | **`0x00361230`** (DT `0x30`,`0x12`,`0x36`) | `0x0012372b` (`0x2b`,`0x37`,`0x12`) |
| +0x20 CID0 | **`0x51`** DPCM 10-8-10 | `0x23` DECODE_10BIT |
| +0x24/+0x28 CID1/2 | **`0x22`** | `0x23` |
| +0x68 irq | **`0x2dd`** (no ECC bit) | after TG-off **`0x20000dd ECC`** |
| +0x70 mapped | **`0x11a`** | `map=0` |

**#146** wrote the WP LUT. Still ECC, `map=0`. Headers fail before LUT.

**#139–#141** matched live WP CSIPHY0 analog (CFG2=`0x3f` CFG3=`0x16`
CFG4=`0xff` CFG5=`0x22` test_imp=`0x17` +0x28 misc1 +0x2c=`0x70`).
After TG-off still `0x20000dd ECC`. **#142** `0xFF03` was never the
live VF. ETL: VF is **`0xFF0B`**. **#143** applied it (2496×1872 PLL
1/124 `0x0820=0x0bd9` stuck); after TG-off still ECC. Do not lottery
other `0xFFxx`.

## Live WP CGC / ISPIF / CAMIF (2026-08-22 evening KD)

Raw: `captures/` CGC session (`dump-idle.log` / `dump-vf.log` / `dump-still.log`).
Idle CAMSS is
powered off (`????????`). VF and after-still are the same (VF resumed).

CAMSS CGC `0xFDA00000` (Hill mux **0**, Ghidra `+0x20/28/30/38/40`):

| Off | VF | Meaning |
|---|---|---|
| +0x00 | `0x60010000` | top |
| +0x10 | `2` | |
| +0x20/28/30/38/40 | **0** | 2-bit selects |
| +0x24 / +0x2c / +0x34 / +0x3c / +0x44 | `0xf` / `0x3f` / `3` / `3` / `3` | enables |

**#148** dumped Linux CGC/MMCC/TCSR during CSIPHY: CGC already matched
WP VF. PHYTIMER `0x107`, CSI0 `0x105`, MCLK `0x3`, TCSR `0x9690e1`.
CSI_VFE0 is **`0x6ff1`** (WP `0x4ff1`). VFE0 RCG **`0x501`** (600 MHz)
vs WP `0x104` (320). Do not flash 320 while CSI is broken. After TG-off
still ECC. Enables were never the leftover poke.

ISPIF VFE0: `+0x244=0` (CSID0), PIX CID mask `+0x254=1`, RDI0 `2`, RDI1 `4`.

CAMIF VF vs Linux bullhead:

| Off | WP VF | Linux HAL |
|---|---|---|
| 0x1C mux | **0** | 0 |
| 0x2E8 input | **`0x17`** | `0x7` |
| 0x2F4 cmd | 1 | 1 |
| 0x2F8 cfg | **`0x001d0040`** | `0x40` |
| 0x2FC EFS | **0** | 0 (#82 EFS killed SOF) |
| 0x300 frame | **2496×1872** | 4080×3028 |
| 0x304/308 win | **0..2495 × 0..1871** | 48..4079 × 2..3025 |
| VFE0 RCG | **320 MHz** (`CFG=0x104`) | 600 MHz |

CSI0 266.67 MHz, phytimer 200 MHz, MCLK 9.6 MHz (ACPI). Next Linux
flash: CAMIF 2496×1872 full window only. Not ECC. Not CGC mux.

Idle block (id 0, 393 regs) is the Sony analog/DPHY table (`0x31a0`, `0x6b4x`, `0xb04x`, `0x31e0`…). That is the remaining original-driver CSI path, not another KMD. Front/iris SMIApp only have the same settle log as rear. `ice5lp`/`icaros` have no CSI strings.
